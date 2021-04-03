from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import Http404, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView
from django.views.generic import DetailView, TemplateView

from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger

from conf.settings import MEDIA_COMPANY_IMAGE_DIR
from vacancies.forms import MyRegistrationForm, MyLoginForm
from vacancies.forms import ApplicationForm, CompanyForm, ResumeForm, VacancyForm
from vacancies.models import Application, Company, Specialty, Resume, Vacancy


#################################################
#                   Основные                    #
#################################################
class Registration(CreateView):
    form_class = MyRegistrationForm
    success_url = '/login'
    template_name = 'vacancies/auth_reg/register.html'


class Login(LoginView):
    form_class = MyLoginForm
    redirect_authenticated_user = True
    template_name = 'vacancies/auth_reg/login.html'


class MainView(TemplateView):
    # главная
    template_name = 'vacancies/main.html'

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        context['specialties'] = Specialty.objects.annotate(count=Count('vacancies__specialty_id'))
        context['companies'] = Company.objects.annotate(count=Count('vacancies__specialty_id'))
        return context


class VacanciesView(ListView):
    # все вакансии
    template_name = 'vacancies/vacancies.html'

    model = Vacancy
    context_object_name = 'vacancies'
    paginate_by = 3

    def get_queryset(self, **kwargs):
        return Vacancy.objects.select_related('company').all()

    def get_context_data(self, **kwargs):
        context = super(VacanciesView, self).get_context_data(**kwargs)
        context['vacancies_count'] = Vacancy.objects.count()
        return context


class VacanciesSpecialtyView(VacanciesView):
    # вакансии по специализации
    def get_queryset(self, **kwargs):
        return Vacancy.objects.select_related('company').filter(specialty_id=self.kwargs['specialty'])

    def get_context_data(self, **kwargs):
        context = super(VacanciesSpecialtyView, self).get_context_data(**kwargs)
        context['specialty'] = get_object_or_404(Specialty, code=self.kwargs['specialty'])
        context['vacancies_count'] = Vacancy.objects.filter(specialty_id=self.kwargs['specialty']).count()
        return context


class CompanyCardView(VacanciesView):
    # карточка компании
    template_name = 'vacancies/company/company.html'

    def get_queryset(self, **kwargs):
        return Vacancy.objects.select_related('company').filter(company_id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(CompanyCardView, self).get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, id=self.kwargs['company_id'])
        return context


class VacancyView(FormMixin, DetailView):
    template_name = 'vacancies/vacancy.html'

    model = Vacancy
    context_object_name = 'vacancy'
    form_class = ApplicationForm

    def get_success_url(self):
        return reverse('vacancy', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
                return self.form_valid(form)
        # else:
        #     return self.form_invalid(form)

    def form_valid(self, form):
        fields = form.save(commit=False)
        fields.user_id = self.request.user.id
        fields.vacancy_id = self.object.pk
        if Application.objects.filter(vacancy_id=self.object.pk).filter(user_id=self.request.user.id):
            fields = form.cleaned_data
            Application.objects.filter(vacancy_id=self.object.pk).filter(user_id=self.request.user.id).update(**fields)
        else:
            form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(VacancyView, self).get_context_data(**kwargs)
        if Application.objects.filter(vacancy_id=self.object.pk).filter(user_id=self.request.user.id):
            context['application_sent'] = True
        return context

    # def form_valid(self, form):
    #     fields = form.save(commit=False)
    #     fields.user_id = self.request.user.id
    #     fields.vacacy_id = self.object
    #     fields.save()
    #     return super().form_valid(form)

    # def get_success_url(self):
    #     return reverse('vacancy', kwargs={'pk': self.object.pk})

    # def post(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     form = self.get_form()
    #
    #     if form.is_valid():
    #         return super(VacancyView, self).form_valid(form)
    #     else:
    #         return self.form_invalid(form)



# def vacancy_view(request, vacancy_id: int):
#     # страница вакансии
#     try:
#         vacancy = Vacancy.objects.select_related('company').get(id=vacancy_id)
#         company = vacancy.company
#     except (Vacancy.DoesNotExist, Company.DoesNotExist):
#         raise Http404
#
#     application_sent = False
#     user_in_application = Application.objects.filter(vacancy_id=vacancy_id).filter(user_id=request.user.id)
#
#     if user_in_application:
#         # если юзер уже отзывался на эту вакансию
#         application_sent = True
#         vacancy_send_form = ApplicationForm(instance=user_in_application.first())
#         if request.method == 'POST':
#             vacancy_send_form = ApplicationForm(request.POST, request.FILES)
#             if vacancy_send_form.is_valid():
#                 vacancy_data = vacancy_send_form.cleaned_data
#                 user_in_application.update(**vacancy_data)
#
#                 return redirect(resume_sending_view, vacancy_id=vacancy.id)
#     else:
#         # пустая форма отклика
#         vacancy_send_form = ApplicationForm()
#         if request.method == 'POST':
#             vacancy_send_form = ApplicationForm(request.POST)
#             if vacancy_send_form.is_valid():
#                 vacancy_send_form_data = vacancy_send_form.cleaned_data
#                 vacancy_send_form_data['user_id'] = request.user.id
#                 vacancy_send_form_data['vacancy_id'] = vacancy.id
#                 Application(**vacancy_send_form_data).save()
#
#                 return redirect(resume_sending_view, vacancy_id=vacancy.id)
#
#
#     context = {
#         'form': vacancy_send_form,
#         'vacancy': vacancy,
#         'company': company,
#         'application_sent': application_sent,
#     }
#
#     return render(request, 'vacancies/vacancy.html', context=context)


def resume_sending_view(request, vacancy_id):
    # отправка отклика на вакансию
    return render(request, 'vacancies/sent.html', {'vacancy_id': vacancy_id})


def search_view(request, query: str):
    pass


#################################################
#                   Компания                    #
#################################################
def my_company_letsstart_view(request):
    # проверка наличия компании
    # если компания ужесоздана
    company_exists = Company.objects.filter(owner_id=request.user.id).values()
    if company_exists:
        return redirect(my_company_view)

    return render(request, 'vacancies/company/company-create.html')


def my_company_empty_view(request):
    # пустая форма компании
    if not request.user.is_authenticated:
        return redirect('login')

    # если компания уже создана
    company_exists = Company.objects.filter(owner_id=request.user.id).values()
    if company_exists:
        return redirect(my_company_view)

    message = ''
    company_form = CompanyForm()
    if request.method == 'POST':
        company_form = CompanyForm(request.POST, request.FILES)
        if company_form.is_valid():
            company_form_update = company_form.save(commit=False)
            company_form_update.owner_id = request.user.id
            company_form.save()
            message = 'success'

    return render(request, 'vacancies/company/company-edit.html', {'form': company_form, 'message': message})


def my_company_view(request):
    # заполненная форма компании
    try:
        company = Company.objects.get(owner_id=request.user.id)
    except Company.DoesNotExist:
        # если в обход меню на /mycompany
        if request.user.is_authenticated:
            return redirect(my_company_letsstart_view)
        else:
            return redirect('login')

    company_form = CompanyForm(instance=company)

    message = ''
    if request.method == 'POST':
        company_form = CompanyForm(request.POST, request.FILES)
        if company_form.is_valid():
            company_data = company_form.cleaned_data
            company_data['logo'] = f"{MEDIA_COMPANY_IMAGE_DIR}/{company_data['logo']}"
            # company_data['logo'] = company_data['logo']

            Company.objects.filter(owner_id=request.user.id).update(**company_data)
            message = 'success'

    return render(request, 'vacancies/company/company-edit.html', {'form': company_form, 'message': message})


def my_vacancies_list_view(request):
    # список моих вакансий
    try:
        company = Company.objects.get(owner_id=request.user.id).id
    except Company.DoesNotExist:
        # если в обход меню на /mycompany/vacancies/
        if request.user.is_authenticated:
            return redirect(my_company_letsstart_view)
        else:
            return redirect('login')

    vacancies = Vacancy.objects.filter(company_id=company)

    return render(request, 'vacancies/company/vacancy-list.html', {'vacancies': vacancies})


def my_vacancy_empty_view(request):
    # пустая форма вакансий
    vacancy_empty_form = VacancyForm()

    message = ''
    if request.method == 'POST':
        vacancy_empty_form = CompanyForm(request.POST)
        if vacancy_empty_form.is_valid():
            vacancy_empty_form.save()
            message = 'success'

    return render(request, 'vacancies/company/vacancy-edit.html', {'form': vacancy_empty_form, 'message': message})


def my_vacancy_view(request, vacancy_id: int):
    # TODO добавить ссылку на профиль откликнувшегося
    # заполненная форма вакансий
    applications = Application.objects.filter(vacancy_id=vacancy_id)

    message = ''
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    my_vacancy_form = VacancyForm(instance=vacancy)

    if request.method == 'POST':
        my_vacancy_form = VacancyForm(request.POST)
        if my_vacancy_form.is_valid():
            company_data = my_vacancy_form.cleaned_data
            Vacancy.objects.filter(id=vacancy_id).update(**company_data)
            message = 'success'

    context = {
        'form': my_vacancy_form,
        'message': message,
        'applications': applications,
    }

    return render(request, 'vacancies/company/vacancy-edit.html', context=context)


#################################################
#                     Резюме                    #
#################################################
def my_resume_letsstart_view(request):
    # предложение создать резюме
    return render(request, 'vacancies/resume/resume-create.html')


def my_resume_empty_view(request):
    # моё резюме пустая форма
    if not request.user.is_authenticated:
        return redirect('login')

    # если резюме уже создано
    resume_exists = Resume.objects.filter(user_id=request.user.id).values()
    if resume_exists:
        return redirect(my_resume_view)

    message = ''
    resume_form = ResumeForm()
    if request.method == 'POST':
        resume_form = ResumeForm(request.POST, request.FILES)
        if resume_form.is_valid():
            resume_form_update = resume_form.save(commit=False)
            resume_form_update.user_id = request.user.id
            resume_form.save()
            message = 'success'

    return render(request, 'vacancies/resume/resume-edit.html', {'form': resume_form, 'message': message})


def my_resume_view(request):
    # моё резюме заполненная форма
    try:
        resume = Resume.objects.get(user_id=request.user.id)
    except Resume.DoesNotExist:
        # если в обход меню на myresume/
        if request.user.is_authenticated:
            return redirect(my_resume_letsstart_view)
        else:
            return redirect('login')

    resume_form = ResumeForm(instance=resume)

    message = ''
    if request.method == 'POST':
        resume_form = ResumeForm(request.POST)
        if resume_form.is_valid():
            resume_data = resume_form.cleaned_data
            Resume.objects.filter(user_id=request.user.id).update(**resume_data)
            message = 'success'

    return render(request, 'vacancies/resume/resume-edit.html', {'form': resume_form, 'message': message})


def custom_handler404(request, exception):
    return HttpResponseNotFound(render(request, '404.html'))


def custom_handler500(request):
    return HttpResponseServerError(render(request, '500.html'))
