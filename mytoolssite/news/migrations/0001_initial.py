# Generated by Django 5.1.7 on 2025-04-05 18:55

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=500)),
                ('source_name', models.CharField(blank=True, help_text='e.g., TechCrunch, OpenAI Blog', max_length=100)),
                ('published_date', models.DateField(db_index=True, default=django.utils.timezone.now)),
                ('added_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'AI News Item',
                'verbose_name_plural': 'AI News Items',
                'ordering': ['-published_date', '-added_date'],
            },
        ),
    ]
