from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wellness', '0011_invitationcode_usage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitationcode',
            name='code',
            field=models.TextField(verbose_name='邀请码'),
        ),
    ]
