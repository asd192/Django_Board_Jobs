# Generated by Django 3.1.6 on 2021-04-17 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0034_auto_20210411_2209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='employee_count',
            field=models.CharField(choices=[('0-15', 'C0 15'), ('15-100', 'C15 100'), ('100-500', 'C100 500'), ('500-1000', 'C500 1000'), ('> 1000', 'C1000')], max_length=10, verbose_name='количество сотрудников'),
        ),
    ]
