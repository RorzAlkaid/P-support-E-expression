from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wellness', '0009_aichatconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('target_role', models.CharField(choices=[('teacher', '教师'), ('admin', '管理员')], max_length=16, verbose_name='邀请角色')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='邀请码')),
                ('is_locked', models.BooleanField(default=True, verbose_name='已锁定')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitation_codes', to=settings.AUTH_USER_MODEL, verbose_name='创建者')),
            ],
            options={
                'verbose_name': '邀请码',
                'verbose_name_plural': '邀请码',
                'ordering': ['target_role', '-updated_at'],
                'unique_together': {('creator', 'target_role')},
            },
        ),
    ]
