# Generated by Django 3.1.6 on 2021-04-11 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0031_auto_20210411_1751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='written_photo',
            field=models.ImageField(blank=True, default=None, upload_to='user_photo', verbose_name='фотография'),
        ),
    ]
