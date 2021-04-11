"""conf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from vacancies.views import CompanyCardView, MainView, UserProfile, VacanciesView, vacancy_view
from vacancies.views import custom_handler404, custom_handler500
from vacancies.views import Login, Registration
from vacancies.views import my_company_delete_view, my_company_empty_view, my_company_view, MyCompanyLetsstarView
from vacancies.views import my_resume_delete, my_resume_empty_view, my_resume_letsstart_view, my_resume_view
from vacancies.views import my_vacancies_list_view, my_vacancy_delete_view, my_vacancy_empty_view, my_vacancy_view
from vacancies.views import ResumesAccessView, ResumeSendingView, ResumesView, SearchView, VacanciesSpecialtyView

handler404 = custom_handler404
handler500 = custom_handler500

urlpatterns = [
    # основные
    path('', MainView.as_view(), name='main'),
    path('vacancies', VacanciesView.as_view(), name='vacancies'),  # все вакансии
    path('resumes', ResumesView.as_view(), name='resumes'),  # все резюме
    path('resumes_access', ResumesAccessView.as_view(), name='resumes_access'),  # все резюме
    path('vacancies/<int:vacancy_id>', vacancy_view, name='vacancy'),  # одна вакансия
    path('vacancies/cat/<str:specialty>', VacanciesSpecialtyView.as_view(), name='vacancies_specialty'),
    path('companies/<int:company_id>', CompanyCardView.as_view(), name='company'),  # компания
    path('vacancies/<int:vacancy_id>/send/', ResumeSendingView.as_view(), name='resume_send'),  # отправка заявки
    path('search', SearchView.as_view(), name='search'),
    path('profile/<int:pk>', UserProfile.as_view(), name='user_profile'),

    # компания
    path('mycompany/letsstart/', MyCompanyLetsstarView.as_view(), name='my_company_letsstart'),  # создать компанию
    path('mycompany/create/', my_company_empty_view, name='my_company_empty_form'),  # пустая форма
    path('mycompany/', my_company_view, name='my_company_form'),  # заполненная форма
    path('mycompany/delete/', my_company_delete_view, name='my_company_delete'),  # удаление компании
    # компания -> вакансии
    path('mycompany/vacancies/', my_vacancies_list_view, name='my_vacancies'),  # мои вакансии - список
    path('mycompany/vacancies/create/', my_vacancy_empty_view, name='my_vacancy_empty_form'),  # пустая форма
    path('mycompany/vacancies/<int:vacancy_id>', my_vacancy_view, name='my_vacancy_form'),  # заполненная форма
    path('mycompany/vacancies/<int:vacancy_id>/delete/', my_vacancy_delete_view, name='my_vacancy_delete'),

    # резюме
    path('myresume/letsstart', my_resume_letsstart_view, name='my_resume_letsstart'),  # предложение создать
    path('myresume/create/', my_resume_empty_view, name='my_resume_empty_form'),  # пустая форма
    path('myresume/', my_resume_view, name='my_resume_form'),  # заполненная форма
    path('myresume/delete', my_resume_delete, name='my_resume_delete'),  # удаление резюме
]

urlpatterns += [
    path('login/', Login.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', Registration.as_view(), name='register'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
