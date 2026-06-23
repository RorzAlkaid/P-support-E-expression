from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wellness', '0007_counselor_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='student_no',
            field=models.CharField(max_length=50, unique=True, verbose_name='学号'),
        ),
    ]
