# Generated manually for external resource crawling support.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wellness', '0003_accountprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='external_url',
            field=models.URLField(blank=True, verbose_name='外部链接'),
        ),
        migrations.AddField(
            model_name='article',
            name='fetched_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='抓取时间'),
        ),
        migrations.CreateModel(
            name='ExternalResourceSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=120, verbose_name='源站名称')),
                ('url', models.URLField(unique=True, verbose_name='源站地址')),
                ('organization', models.CharField(blank=True, max_length=120, verbose_name='机构')),
                ('category', models.CharField(default='心理科普', max_length=40, verbose_name='默认分类')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='默认标签')),
                ('enabled', models.BooleanField(default=True, verbose_name='启用')),
                ('last_fetched_at', models.DateTimeField(blank=True, null=True, verbose_name='上次抓取时间')),
            ],
            options={
                'verbose_name': '外部资源源站',
                'verbose_name_plural': '外部资源源站',
            },
        ),
        migrations.CreateModel(
            name='ResourceFetchLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('status', models.CharField(choices=[('success', '成功'), ('failed', '失败'), ('skipped', '跳过')], max_length=16, verbose_name='状态')),
                ('message', models.TextField(blank=True, verbose_name='信息')),
                ('articles_created', models.PositiveIntegerField(default=0, verbose_name='新增文章数')),
                ('articles_updated', models.PositiveIntegerField(default=0, verbose_name='更新文章数')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fetch_logs', to='wellness.externalresourcesource', verbose_name='源站')),
            ],
            options={
                'verbose_name': '资源抓取记录',
                'verbose_name_plural': '资源抓取记录',
                'ordering': ['-created_at'],
            },
        ),
    ]
