import os
import django


os.environ["DJANGO_SETTINGS_MODULE"] = 'conf.settings'
django.setup()


if __name__ == '__main__':
    # from django.contrib.auth.models import User
    # pass_ = User.objects.get(username='admin')
    # pass_.set_password('admin')
    # pass_.save()
    from vacancies.models import Vacancy, Application
    from django.db.models import Count

    # applcations = Application.objects.select_related('vacancy').filter(vacancy__company_id=1)
    vacancies = Vacancy.objects.filter(company_id=1).annotate(application_count=Count('applications'))

    for vacancy in vacancies:
        print(vacancy.application_count)

    # print(applcations.values_list())

