from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView

from conf.settings import MEDIA_COMPANY_IMAGE_DIR
from vacancies.forms import ApplicationForm, CompanyForm, ResumeForm, VacancyForm
from vacancies.forms import MyRegistrationForm, MyLoginForm
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
        return self.model.objects.select_related('company').all()

    def get_context_data(self, **kwargs):
        context = super(VacanciesView, self).get_context_data(**kwargs)
        context['vacancies_count'] = Vacancy.objects.count()
        return context


class VacanciesSpecialtyView(VacanciesView):
    # вакансии по специализации
    def get_queryset(self, **kwargs):
        return self.model.objects.select_related('company').filter(specialty_id=self.kwargs['specialty'])

    def get_context_data(self, **kwargs):
        context = super(VacanciesSpecialtyView, self).get_context_data(**kwargs)
        context['specialty'] = get_object_or_404(Specialty, code=self.kwargs['specialty'])
        context['vacancies_count'] = Vacancy.objects.filter(specialty_id=self.kwargs['specialty']).count()
        return context


class SearchView(VacanciesView):
    # поиск вакансий
    template_name = 'vacancies/search.html'

    def get_queryset(self):
        request_user = self.request.GET.get('s')
        return self.model.objects.select_related('company').filter(
            Q(title__icontains=request_user) | Q(description__icontains=request_user)
        )

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['s'] = self.request.GET.get('s')
        context['vacancies_count'] = context['paginator'].count
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
    # вакансия
    template_name = 'vacancies/vacancy.html'
    model = Vacancy
    context_object_name = 'vacancy'
    form_class = ApplicationForm

    def application(self):
        vacancies = Application.objects.filter(vacancy_id=self.object.pk).filter(user_id=self.request.user.id)
        return vacancies

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return super().form_invalid(form)

    def form_valid(self, form):
        fields = form.save(commit=False)
        fields.user_id = self.request.user.id
        fields.vacancy_id = self.object.pk
        if self.application:
            fields = form.cleaned_data
            self.application().update(**fields)
        else:
            form.save()
        return redirect('resume_send', vacancy_id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(VacancyView, self).get_context_data(**kwargs)
        if self.application:
            context['application_sent'] = True
        return context


class ResumeSendingView(TemplateView):
    template_name = 'vacancies/sent.html'


#################################################
#                   Компания                    #
#################################################
class MyCompanyLetsstarView(View):
    template_name = 'vacancies/company/company-create.html'

    def get(self, request, *args, **kwargs):
        if Company.objects.filter(owner_id=request.user.id).values():
            return redirect('my_company_form')
        else:
            return render(request, 'vacancies/company/company-create.html')


class MyCompanyEmptyFormView(CreateView):
    template_name = 'vacancies/company/company-edit.html'
    form_class = CompanyForm

    def get_success_url(self):
        return redirect('my_company_letsstart')

    def form_valid(self, form):
        fields = form.save(commit=False)
        fields.owner_id = self.request.user.id
        form.save()
        return redirect('my_company_letsstart')


class MyCompanyFormView(UpdateView):
    template_name = 'vacancies/company/company-edit.html'
    form_class = CompanyForm


# def my_company_view(request):
#     # заполненная форма компании
#     try:
#         company = Company.objects.get(owner_id=request.user.id)
#     except Company.DoesNotExist:
#         # если в обход меню на /mycompany
#         if request.user.is_authenticated:
#             return redirect('my_company_letsstart')
#         else:
#             return redirect('login')
#
#     company_form = CompanyForm(instance=company)
#
#     message = ''
#     if request.method == 'POST':
#         company_form = CompanyForm(request.POST, request.FILES)
#         if company_form.is_valid():
#             company_data = company_form.cleaned_data
#             # company_data['logo'] = f"{MEDIA_COMPANY_IMAGE_DIR}/{company_data['logo']}"
#             # company_data['logo'] = company_data['logo']
#
#             Company.objects.filter(owner_id=request.user.id).update(**company_data)
#             message = 'success'
#
#     return render(request, 'vacancies/company/company-edit.html', {'form': company_form, 'message': message})


def my_vacancies_list_view(request):
    # список моих вакансий
    try:
        company = Company.objects.get(owner_id=request.user.id).id
    except Company.DoesNotExist:
        # если в обход меню на /mycompany/vacancies/
        if request.user.is_authenticated:
            return redirect('my_company_letsstart')
        else:
            return redirect('login')

    vacancies = Vacancy.objects.filter(company_id=company)
    # vacancies = Application.objects.select_related('vacancy').exclude(vacancy__company_id=3)
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
    # заполненная форма вакансий
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    applications = Application.objects.filter(vacancy_id=vacancy_id)

    message = ''
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
