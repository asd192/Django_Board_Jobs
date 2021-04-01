from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import Http404, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import CreateView

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
    template_name = 'vacancy/auth_reg/register.html'


class Login(LoginView):
    form_class = MyLoginForm
    redirect_authenticated_user = True
    template_name = 'vacancy/auth_reg/login.html'


def main_view(request):
    # главная страница
    specialties = Specialty.objects.values('code', 'title', 'picture').annotate(count=Count('vacancies__specialty_id'))
    companies = Company.objects.values('id', 'logo', 'name').annotate(count=Count('vacancies__specialty_id'))

    return render(request, 'vacancy/main.html', {'specialties': specialties[:8], 'companies': companies[:8]})


def vacancy_list_view(request):
    # все вакансии списком
    vacancies = Vacancy.objects.values(
        'id', 'title', 'skills', 'salary_min', 'salary_max', 'published_at', 'company_id', 'company__name',
        'company__logo',
    )

    return render(request, 'vacancy/vacancies.html', {'vacancies': vacancies})


def vacancies_specialization_view(request, specialization: str):
    # все вакансии по специализации
    vacancies = Vacancy.objects.filter(specialty_id=specialization).values(
        'id', 'title', 'skills', 'salary_min', 'salary_max', 'published_at', 'company_id', 'company__logo',
        'specialty__title',
    )

    if vacancies:
        specialization_title = vacancies[0]['specialty__title']
    else:
        specialization_title = get_object_or_404(Specialty, code=specialization).title

    return render(request, 'vacancy/vacancies.html', {'vacancies': vacancies, 'title': specialization_title})


def company_card_view(request, company_id: int):
    # карточка компании
    company = get_object_or_404(Company, id=company_id)

    vacancies = Vacancy.objects.filter(company_id=company_id).values(
        'id', 'title', 'skills', 'salary_min', 'salary_max', 'published_at', 'company__logo', 'company__name',
    )

    return render(request, 'vacancy/company/company.html', {'vacancies': vacancies, 'company': company})


def vacancy_view(request, vacancy_id: int):
    # страница вакансии
    try:
        vacancy = Vacancy.objects.select_related('company').get(id=vacancy_id)
        company = vacancy.company
    except (Vacancy.DoesNotExist, Company.DoesNotExist):
        raise Http404

    application_sent = False
    user_in_application = Application.objects.filter(vacancy_id=vacancy_id).filter(user_id=request.user.id)

    if user_in_application:
        # если юзер уже отзывался на эту вакансию
        application_sent = True
        vacancy_send_form = ApplicationForm(instance=user_in_application.first())
        if request.method == 'POST':
            vacancy_send_form = ApplicationForm(request.POST, request.FILES)
            if vacancy_send_form.is_valid():
                vacancy_data = vacancy_send_form.cleaned_data
                user_in_application.update(**vacancy_data)

                return redirect(resume_sending_view, vacancy_id=vacancy.id)
    else:
        # пустая форма отклика
        vacancy_send_form = ApplicationForm()
        if request.method == 'POST':
            vacancy_send_form = ApplicationForm(request.POST)
            if vacancy_send_form.is_valid():
                vacancy_send_form_data = vacancy_send_form.cleaned_data
                vacancy_send_form_data['user_id'] = request.user.id
                vacancy_send_form_data['vacancy_id'] = vacancy.id
                Application(**vacancy_send_form_data).save()

                return redirect(resume_sending_view, vacancy_id=vacancy.id)

            # elif 'written_phone' not in vacancy_send_form.cleaned_data:
            #     vacancy_send_form.add_error('written_phone', 'Еще примеры: +7 999 555 33 11')

    context = {
        'form': vacancy_send_form,
        'vacancy': vacancy,
        'company': company,
        'application_sent': application_sent,
    }

    return render(request, 'vacancy/vacancy.html', context=context)


def resume_sending_view(request, vacancy_id):
    # отправка отклика на вакансию
    return render(request, 'vacancy/sent.html', {'vacancy_id': vacancy_id})


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

    return render(request, 'vacancy/company/company-create.html')


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

    return render(request, 'vacancy/company/company-edit.html', {'form': company_form, 'message': message})


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

    return render(request, 'vacancy/company/company-edit.html', {'form': company_form, 'message': message})


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

    return render(request, 'vacancy/company/vacancy-list.html', {'vacancies': vacancies})


def my_vacancy_empty_view(request):
    # пустая форма вакансий
    vacancy_empty_form = VacancyForm()

    message = ''
    if request.method == 'POST':
        vacancy_empty_form = CompanyForm(request.POST)
        if vacancy_empty_form.is_valid():
            vacancy_empty_form.save()
            message = 'success'

    return render(request, 'vacancy/company/vacancy-edit.html', {'form': vacancy_empty_form, 'message': message})


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

    return render(request, 'vacancy/company/vacancy-edit.html', context=context)


#################################################
#                     Резюме                    #
#################################################
def my_resume_letsstart_view(request):
    # предложение создать резюме
    return render(request, 'vacancy/resume/resume-create.html')


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

    return render(request, 'vacancy/resume/resume-edit.html', {'form': resume_form, 'message': message})


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

    return render(request, 'vacancy/resume/resume-edit.html', {'form': resume_form, 'message': message})


def custom_handler404(request, exception):
    return HttpResponseNotFound(render(request, '404.html'))


def custom_handler500(request):
    return HttpResponseServerError(render(request, '500.html'))
