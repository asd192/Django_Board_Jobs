from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.db.models import Q
from django.http import Http404, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView, View
from django.views.generic.list import ListView

import vacancies.models
from vacancies.forms import ApplicationForm, CompanyForm, ResumeForm, VacancyForm
from vacancies.forms import MyLoginForm, MyRegistrationForm, UserProfileForm
from vacancies.models import Application, Company, Resume, Specialty, Vacancy


#################################################
#                   Основные                    #
#################################################
class Registration(CreateView):
    form_class = MyRegistrationForm
    success_url = '/login'
    template_name = 'vacancies/auth_reg/register.html'

    def form_valid(self, form):
        messages.success(self.request, 'Успешная регистрация. Заходите')
        return super(Registration, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Регистрация не удалась. Проверьте правильность заполнения полей')
        return super(Registration, self).form_invalid(form)


class Login(LoginView):
    form_class = MyLoginForm
    redirect_authenticated_user = True
    template_name = 'vacancies/auth_reg/login.html'

    def form_invalid(self, form):
        messages.error(self.request, 'Не удалось войти. Проверьте правильность заполнения полей')
        return super(Login, self).form_invalid(form)


class UserProfile(LoginRequiredMixin, UpdateView):
    """Профиль пользователя"""
    template_name = 'vacancies/profile.html'
    model = User
    form_class = UserProfileForm

    def get_success_url(self):
        return reverse_lazy('user_profile', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Информация о профиле обновлена')
        return super(UserProfile, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Проверьте правильность заполнения формы')
        return super(UserProfile, self).form_invalid(form)


class MainView(TemplateView):
    """Главная"""
    template_name = 'vacancies/main.html'

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        context['specialties'] = Specialty.objects.annotate(count=Count('vacancies__specialty_id'))[:8]
        context['companies'] = Company.objects.annotate(count=Count('vacancies__specialty_id'))[:8]
        return context


class VacanciesView(ListView):
    """Все вакансии"""
    template_name = 'vacancies/vacancies.html'
    model = Vacancy
    context_object_name = 'vacancies'
    paginate_by = 3

    def get_queryset(self, **kwargs):
        return self.model.objects.select_related('company').all()

    def get_context_data(self, **kwargs):
        context = super(VacanciesView, self).get_context_data(**kwargs)
        context['vacancies_count'] = Vacancy.objects.count()
        return context


class VacanciesSpecialtyView(VacanciesView):
    """Вакансии по специализации"""

    def get_queryset(self, **kwargs):
        return self.model.objects.select_related('company').filter(specialty_id=self.kwargs['specialty'])

    def get_context_data(self, **kwargs):
        context = super(VacanciesSpecialtyView, self).get_context_data(**kwargs)
        context['specialty'] = get_object_or_404(Specialty, code=self.kwargs['specialty'])
        context['vacancies_count'] = Vacancy.objects.filter(specialty_id=self.kwargs['specialty']).count()
        return context


class ResumesView(ListView):
    """Все резюме"""
    template_name = 'vacancies/resumes.html'
    model = Resume
    context_object_name = 'resumes'
    paginate_by = 3

    def get(self, request, *args, **kwargs):
        try:
            Company.objects.get(owner_id=request.user.id)
        except Company.DoesNotExist:
            return redirect('resumes_access')
        else:
            return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ResumesView, self).get_context_data(**kwargs)
        context['resumes_count'] = Resume.objects.count()
        return context


class ResumesAccessView(TemplateView):
    template_name = 'vacancies/resumes-access.html'


class SearchView(VacanciesView):
    """Поиск вакансий(строка поиска)"""
    template_name = 'vacancies/search.html'

    def get_queryset(self):
        request_user = self.request.GET.get('s')
        return self.model.objects.select_related('company').filter(
            Q(title__icontains=request_user) | Q(description__icontains=request_user),
        )

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['s'] = self.request.GET.get('s')
        context['vacancies_count'] = context['paginator'].count
        return context


class CompanyCardView(VacanciesView):
    """Карточка компании"""
    template_name = 'vacancies/company/company.html'

    def get_queryset(self, **kwargs):
        return Vacancy.objects.select_related('company').filter(company_id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(CompanyCardView, self).get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, id=self.kwargs['company_id'])
        return context


class VacancyView(CreateView):
    """Страница вакансии + отклик"""
    template_name = 'vacancies/vacancy.html'
    model = Vacancy
    form_class = ApplicationForm

    def get_success_url(self, **kwargs):
        return reverse_lazy('resume_send', kwargs={'vacancy_id': self.kwargs['vacancy_id']})

    def get_context_data(self, **kwargs):
        context = super(VacancyView, self).get_context_data(**kwargs)

        user_in_application = Application.objects.filter(
            vacancy_id=self.kwargs['vacancy_id'],
            user_id=self.request.user.id,
        )
        context['application_sent'] = user_in_application
        context['vacancy'] = self.model.objects.select_related('company').get(id=self.kwargs['vacancy_id'])

        if user_in_application:
            messages.info(self.request, 'Вы уже отзывались на эту вакансию')

        return context

    def form_valid(self, form):
        form_add = form.save(commit=False)
        form_add.vacancy_id = self.kwargs['vacancy_id']
        form_add.user_id = self.request.user.id
        form.save()

        messages.success(self.request, 'Отклик успешно отправлен')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Не удалось отправить отклик. Проверьте правильность запонения формы')
        return super().form_invalid(form)


class ResumeSendingView(TemplateView):
    """Подтверждение отправленного резюме"""
    template_name = 'vacancies/sent.html'


#################################################
#                   Компания                    #
#################################################
class MyCompanyLetsstarView(View):
    """Предложение создать компанию"""
    template_name = 'vacancies/company/company-create.html'

    def get(self, request, *args, **kwargs):
        if Company.objects.filter(owner_id=request.user.id).values():
            return redirect('my_company_form')
        return render(request, 'vacancies/company/company-create.html')


class MyCompanyCreateView(LoginRequiredMixin, CreateView):
    """Пустая форма моей компании"""
    template_name = 'vacancies/company/company-edit.html'
    model = Company
    form_class = CompanyForm

    def get_success_url(self):
        return reverse_lazy('my_company_letsstart')

    def form_valid(self, form):
        form_add = form.save(commit=False)
        form_add.owner_id = self.request.user.id
        form.save()

        messages.success(self.request, 'Компания успешно создана')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Проверьте правильность заполнения формы')
        return super().form_invalid(form)


class MyCompanyView(LoginRequiredMixin, UpdateView):
    """Заполненная форма моей компании"""
    template_name = 'vacancies/company/company-edit.html'
    model = Company
    form_class = CompanyForm

    def get_success_url(self):
        return reverse_lazy('my_company_letsstart')

    def get_object(self, queryset=None):
        return get_object_or_404(Company, owner_id=self.request.user.id)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Информация о компании успешно обновлена')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Не удалось обновить. Проверьте правильность заполнения формы')
        return super().form_invalid(form)


class MyCompanyDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление компании"""
    model = Company
    success_url = reverse_lazy("my_company_letsstart")

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.get_queryset().get(owner_id=self.request.user.id).get()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Компания удалена')
        return super(MyCompanyDeleteView, self).delete(request, *args, **kwargs)


class MyVacanciesView(LoginRequiredMixin, ListView):
    """Мои вакансии"""
    template_name = 'vacancies/company/vacancy-list.html'
    model = Vacancy
    context_object_name = 'vacancies'

    def get_queryset(self):
        company_id = get_object_or_404(Company, owner_id=self.request.user.id)
        return Vacancy.objects.filter(company_id=company_id).annotate(application_count=Count('applications'))


class MyVacancyCreateView(LoginRequiredMixin, CreateView):
    """Пустая форма вакансии"""
    template_name = 'vacancies/company/vacancy-edit.html'
    model = Vacancy
    form_class = VacancyForm

    def get_success_url(self, **kwargs):
        return reverse_lazy('my_vacancies')

    def form_valid(self, form):
        form_add = form.save(commit=False)
        form_add.company_id = Company.objects.get(owner_id=self.request.user.id).id
        form.save()

        messages.success(self.request, 'Вакансия успешно создана')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Проверьте правильность заполнения формы')
        return super().form_invalid(form)


class MyVacancyView(LoginRequiredMixin, UpdateView):
    """Заполненная форма вакансии"""
    template_name = 'vacancies/company/vacancy-edit.html'
    model = Vacancy
    form_class = VacancyForm
    pk_url_kwarg = 'vacancy_id'

    def get_object(self, queryset=None):
        vacancy = get_object_or_404(Vacancy, id=self.kwargs['vacancy_id'])
        company_user = get_object_or_404(Company, owner_id=self.request.user.id)
        print(vacancy.company_id, company_user.id)
        # проверка, что компания принадлежит юзеру
        if vacancy.company_id != company_user.id:
            raise Http404
        return vacancy

    def get_context_data(self, **kwargs):
        context = super(MyVacancyView, self).get_context_data(**kwargs)
        context['vacancy_exists'] = self.kwargs['vacancy_id']
        return context

    def get_success_url(self):
        return reverse_lazy('my_vacancy_form', kwargs={'vacancy_id': self.kwargs['vacancy_id']})

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Информация о вакансии успешно обновлена')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Не удалось обновить вакансию. Проверьте правильность заполнения формы')
        return super().form_invalid(form)


class MyVacancyDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление вакансии"""
    model = Vacancy
    success_url = reverse_lazy("my_vacancies")
    pk_url_kwarg = 'vacancy_id'

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def get_object(self, queryset=None):
        vacnacy = get_object_or_404(Vacancy, id=self.kwargs['vacancy_id'])
        company_user = get_object_or_404(Company, owner_id=self.request.user.id)
        if vacnacy.company_id != company_user.id:
            raise Http404
        return vacnacy

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Вакансия удалена')
        return super(MyVacancyDeleteView, self).delete(request, *args, **kwargs)


#################################################
#                     Резюме                    #
#################################################
class MyResumeLetsstartView(LoginRequiredMixin, View):
    """Резюме, редложение создать"""

    def get(self, request, *args, **kwargs):
        if Resume.objects.filter(user_id=request.user.id):
            return redirect('my_resume_form')
        return render(request, 'vacancies/resume/resume-create.html')


class MyResumeCreateView(LoginRequiredMixin, CreateView):
    """Пустая форма резюме"""
    template_name = 'vacancies/resume/resume-edit.html'
    model = Resume
    form_class = ResumeForm

    def get_success_url(self, **kwargs):
        return reverse_lazy('my_resume_form')

    def form_valid(self, form):
        form_add = form.save(commit=False)
        form_add.user_id = self.request.user.id
        form.save()

        messages.success(self.request, 'Резюме успешно создано')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Проверьте правильность заполнения формы')
        return super().form_invalid(form)


class MyResumeView(LoginRequiredMixin, UpdateView):
    """Заполненная форма резюме"""
    template_name = 'vacancies/resume/resume-edit.html'
    model = Resume
    form_class = ResumeForm

    def get_success_url(self):
        return reverse_lazy('my_vacancy_form', kwargs={'vacancy_id': self.kwargs['vacancy_id']})

    def get_object(self, queryset=None):
        return get_object_or_404(Resume, user_id=self.request.user.id)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Информация о резюме успешно обновлена')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Не удалось обновить резюме. Проверьте правильность заполнения формы')
        return super().form_invalid(form)


class MyResumeDeleteView(LoginRequiredMixin, DeleteView):
    model = Resume
    success_url = reverse_lazy("my_resume_letsstart")
    pk_url_kwarg = 'user_id'

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def get_object(self, queryset=None):
        resume = get_object_or_404(Resume, user_id=self.kwargs['user_id'])
        return resume

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Резюме удалено')
        return super(MyResumeDeleteView, self).delete(request, *args, **kwargs)


def custom_handler404(request, exception):
    return HttpResponseNotFound(render(request, '404.html'))


def custom_handler500(request):
    return HttpResponseServerError(render(request, '500.html'))
