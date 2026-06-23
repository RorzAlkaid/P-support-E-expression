from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wellness', '0006_resourceviewlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='counselor',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='counselor_profile',
                to=settings.AUTH_USER_MODEL,
                verbose_name='关联教师账号',
            ),
        ),
    ]
