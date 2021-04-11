from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from conf.settings import MEDIA_COMPANY_IMAGE_DIR, MEDIA_SPECIALITY_IMAGE_DIR, MEDIA_USER_PHOTO_IMAGE_DIR


class Specialty(models.Model):
    code = models.CharField("код", primary_key=True, max_length=30)
    title = models.CharField("название", max_length=100)
    picture = models.ImageField("изображение", upload_to=MEDIA_SPECIALITY_IMAGE_DIR,
                                default=f'{MEDIA_SPECIALITY_IMAGE_DIR}/100x60.gif')

    class Meta:
        verbose_name = "специализация"
        verbose_name_plural = "специализации"

    def __str__(self):
        return f"{self.title}"


class Company(models.Model):
    CHOICES_EMPLOYEE_COUNT = (
        ('1', '0-15'),
        ('2', '15-100'),
        ('3', '100-500'),
        ('4', '500-1000'),
        ('5', '> 1000'),
    )

    name = models.CharField("название", max_length=100)
    location = models.CharField("город", max_length=25)
    description = models.TextField("информация о компании", max_length=5000)
    employee_count = models.CharField("количество сотрудников", max_length=10, choices=CHOICES_EMPLOYEE_COUNT)
    logo = models.ImageField("логотип", upload_to=MEDIA_COMPANY_IMAGE_DIR,
                             default=f'{MEDIA_COMPANY_IMAGE_DIR}/100x60.gif')
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="owner_user", verbose_name="owner_id")

    def employee_count_verbose(self):
        """Значение списка. Использование в шаблоне -> {{ model.employee_count_verbose }}"""
        return dict(Company.CHOICES_EMPLOYEE_COUNT)[self.employee_count]

    class Meta:
        verbose_name = "компания"
        verbose_name_plural = "компании"

    def __str__(self):
        return f"{self.name}"


class Vacancy(models.Model):
    title = models.CharField("название вакансии", max_length=100, db_index=True)
    skills = models.CharField("навыки", max_length=500)
    description = models.TextField("описание вакансии", max_length=10000, db_index=True)
    salary_min = models.IntegerField("зарплата от")
    salary_max = models.IntegerField("зарплата до")
    published_at = models.DateField("опубликовано", auto_now_add=True)
    company = models.ForeignKey(Company,
                                on_delete=models.CASCADE, related_name="vacancies", verbose_name="компания")
    specialty = models.ForeignKey(Specialty,
                                  on_delete=models.PROTECT, related_name="vacancies", verbose_name="специализация")

    class Meta:
        verbose_name = "вакансия"
        verbose_name_plural = "вакансии"
        ordering = ['id']

    def __str__(self):
        return f"{self.title}"


class Application(models.Model):
    written_username = models.CharField("имя", max_length=50)
    written_phone = PhoneNumberField("номер телефона", region='RU')
    written_cover_letter = models.TextField("сопроводительное письмо", max_length=10000)
    written_photo = models.ImageField(
        "фотография", upload_to=MEDIA_USER_PHOTO_IMAGE_DIR, blank=True, default=None,
    )
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="applications")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="applications", null=True)

    class Meta:
        verbose_name = "отклик"
        verbose_name_plural = "отклики"

    def __str__(self):
        return self.written_username


class Resume(models.Model):
    CHOICES_STATUS = (
        ('1', 'Не ищу работу'),
        ('2', 'Рассматриваю предложения'),
        ('3', 'Ищу работу'),
    )

    CHOICES_GRADE = (
        ('1', 'Стажер'),
        ('2', 'Джуниор'),
        ('3', 'Миддл'),
        ('4', 'Синьор'),
        ('5', 'Лид'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="resumes")
    name = models.CharField("имя", max_length=15)
    surname = models.CharField("фамилия", max_length=30)
    status = models.CharField("готовность к работе", max_length=10, choices=CHOICES_STATUS)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, max_length=30, verbose_name="специализация")
    salary = models.IntegerField("ожидаемое вознаграждение")
    grade = models.CharField("квалификация", max_length=10, choices=CHOICES_GRADE)
    education = models.TextField("образование", max_length=1000)
    experience = models.TextField("опыт работы", max_length=1000)
    portfolio = models.URLField("ссылка на портфолио", max_length=100)

    def status_verbose(self):
        return dict(Resume.CHOICES_STATUS)[self.status]

    def grade_verbose(self):
        return dict(Resume.CHOICES_GRADE)[self.grade]

    class Meta:
        verbose_name = "резюме"
        verbose_name_plural = "резюме"
        ordering = ['id']

    def __str__(self):
        return f"{self.surname} {self.name}"
