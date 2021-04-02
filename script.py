import os
import django


os.environ["DJANGO_SETTINGS_MODULE"] = 'conf.settings'
django.setup()


if __name__ == '__main__':
    # from django.contrib.auth.models import User
    # pass_ = User.objects.get(username='admin')
    # pass_.set_password('admin')
    # pass_.save()
    from vacancies.models import Application, Company, Specialty, Resume, Vacancy
    print(Vacancy.objects.select_related('company').all())