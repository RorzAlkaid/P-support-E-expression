# Generated manually for counselor public directory sync support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wellness', '0004_external_resources'),
    ]

    operations = [
        migrations.AddField(
            model_name='counselor',
            name='source',
            field=models.CharField(blank=True, max_length=120, verbose_name='来源'),
        ),
        migrations.AddField(
            model_name='counselor',
            name='external_url',
            field=models.URLField(blank=True, verbose_name='外部链接'),
        ),
        migrations.AddField(
            model_name='counselor',
            name='fetched_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='抓取时间'),
        ),
    ]
