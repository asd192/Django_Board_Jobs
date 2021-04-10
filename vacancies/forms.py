from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, HTML, Layout, Row, Submit
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.contrib.auth.models import User

from vacancies.models import Application, Company, Resume, Vacancy


class MyRegistrationForm(UserCreationForm):
    username = UsernameField(label='Логин', min_length=3, max_length=15)
    first_name = forms.CharField(label='Имя', min_length=2, max_length=20)
    last_name = forms.CharField(label='Фамилия', min_length=3, max_length=30)
    email = forms.EmailField(label='Email', min_length=6, max_length=50)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Не менее 3-ёх символов'
        self.fields['email'].help_text = 'Ваш электронный почтовый ящик'
        self.fields['first_name'].help_text = 'Не менее 2-ух букв'
        self.fields['last_name'].help_text = 'Не менее 3-ёх букв'
        self.fields['password1'].help_text = 'Придумайте надёжный пароль не менее 8 символов.'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Регистрация'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


class MyLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Введите ваш логин'
        self.fields['password'].help_text = 'Введите ваш пароль'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Войти'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'


class CompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = 'Не более 100 символов'
        self.fields['location'].help_text = 'Не более 25 символов'
        self.fields['employee_count'].help_text = 'Выберите вариант'
        self.fields['description'].help_text = 'Опишите чем занимается компания'
        self.fields['logo'].help_text = 'Логотип компании'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'

        self.helper.layout = Layout(
            Row(
                Column(
                    HTML(
                        '''
                        <div class="row">
                            <div class="mx-auto">{% if form.logo.value %}<img src="{{ form.logo.value.url }}"{% endif %}
                                width="140 height="60">
                            </div>
                        </div>
                        ''',
                    ),
                    Column('logo', css_class='form-group'),
                ),
            ),
            Row(
                Column('name', css_class='form-group'),
                css_class='form-row',
            ),
            Row(
                Column('employee_count', css_class='form-group'),
                Column('location', css_class='form-group'),
                css_class='form-row',
            ),
            'description',
        )

    class Meta:
        model = Company
        fields = ("logo", "name", "location", "description", "employee_count")


class VacancyForm(forms.ModelForm):
    skills = forms.RegexField(
        regex=r'^[а-яА-Яa-zA-Z0-9,. ]*$',
        error_messages={'invalid': 'Допускаются только БУКВЫ, ЦИФРЫ, ТОЧКИ, ЗАПЯТЫЕ и ПРОБЕЛЫ'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].help_text = 'Максимум 100 символов'
        self.fields['skills'].help_text = 'Укажите список через запятую. Пример: Swift, CoreData, Git, ООП'
        self.fields['salary_min'].help_text = 'Минимальная оплата'
        self.fields['salary_max'].button_text = 'Максимальная оплата'
        self.fields['specialty'].button_text = 'Выберите значение'
        self.fields['description'].help_text = 'Не более 10 000 символов'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'

        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group'),
                Column('specialty', css_class='form-group'),
                css_class='form-row',
            ),
            Row(
                Column('salary_min', css_class='form-group'),
                Column('salary_max', css_class='form-group'),
                css_class='form-row',
            ),
            'skills',
            'description',
        )

    class Meta:
        model = Vacancy
        fields = ("title", "specialty", "salary_min", "salary_max", "skills", "description")


class ApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['written_username'].label = 'ФИО'
        self.fields['written_username'].help_text = 'Ваши настоящие ФИО'
        self.fields['written_phone'].help_text = 'Номер телефона'
        self.fields['written_cover_letter'].help_text = 'Не более 10 000 символов'
        self.fields['written_photo'].help_text = 'Загрузите ваше фото(по желанию)'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Отправить'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'

    class Meta:
        model = Application
        fields = ('written_username', 'written_phone', 'written_cover_letter', 'written_photo')
        error_messages = {
            'written_phone': {'invalid': 'Введите корректный номер телефона. Пример: +79991115533'},
        }


class ResumeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'

        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group'),
                Column('surname', css_class='form-group'),
                css_class='form-row',
            ),
            Row(
                Column('status', css_class='form-group'),
                Column('salary', css_class='form-group'),
                css_class='form-row',
            ),
            Row(
                Column('specialty', css_class='form-group'),
                Column('grade', css_class='form-group'),
                css_class='form-row',
            ),
            'education',
            'experience',
            'portfolio',
        )

    class Meta:
        model = Resume
        fields = ("name", "surname", "status", "salary", "specialty", "grade", "education", "experience", "portfolio")


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(min_length=5, max_length=50, disabled=True)
    first_name = forms.CharField(min_length=2, max_length=15)
    last_name = forms.CharField(min_length=2, max_length=25)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Обновить'))

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'pb-1'
        self.helper.field_class = 'col-12'

        self.helper.layout = Layout(
            'email',
            Row(
                Column('first_name', css_class='form-group'),
                Column('last_name', css_class='form-group'),
                css_class='form-row',
            ),
        )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")
