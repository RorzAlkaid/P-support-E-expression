# Generated manually for student resource view tracking.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wellness', '0005_counselor_external_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceViewLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('article_title', models.CharField(max_length=120, verbose_name='article title')),
                ('article_source', models.CharField(blank=True, max_length=120, verbose_name='article source')),
                ('article_category', models.CharField(blank=True, max_length=40, verbose_name='article category')),
                ('article', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='view_logs', to='wellness.article', verbose_name='article')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resource_view_logs', to='wellness.studentprofile', verbose_name='student')),
            ],
            options={
                'verbose_name': 'resource view log',
                'verbose_name_plural': 'resource view logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
