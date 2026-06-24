from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wellness', '0010_invitationcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitationcode',
            name='used_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='使用时间'),
        ),
        migrations.AddField(
            model_name='invitationcode',
            name='used_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_invitation_codes', to=settings.AUTH_USER_MODEL, verbose_name='使用者'),
        ),
    ]
