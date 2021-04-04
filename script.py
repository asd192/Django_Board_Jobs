import os
import django


os.environ["DJANGO_SETTINGS_MODULE"] = 'conf.settings'
django.setup()


if __name__ == '__main__':
    # from django.contrib.auth.models import User
    # pass_ = User.objects.get(username='admin')
    # pass_.set_password('admin')
    # pass_.save()
    from django.db.models import Count
    from vacancies.models import Application, Company, Specialty, Resume, Vacancy
    # print(Application.objects.select_related('vacancy').filter(vacancy__company_id=1).annotate(count=Count('vacancy_id')).first())
    # x = Vacancy.objects.select_related('company__owner__applications').filter(company_id=1)
    # for i in x:
    #     print(i.applications.values())

    # x = Application.objects.select_related('vacancy').exclude(vacancy__company_id=3).annotate(count=Count('vacancy'))
    vacancies = Vacancy.objects.filter(company_id=1).select_related('applications').annotate(count=Count('vacancy_id'))
    for i in vacancies:
        print(i)


