# Generated migration to add missing is_on_pilot column

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='is_on_pilot',
            field=models.BooleanField(default=True),
        ),
    ]