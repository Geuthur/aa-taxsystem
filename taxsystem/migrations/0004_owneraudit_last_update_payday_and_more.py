# Generated by Django 4.2.11 on 2025-04-01 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxsystem", "0003_alter_general_options_alter_paymenthistory_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="owneraudit",
            name="last_update_payday",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="paymentsystem",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("deactivated", "Deactivated"),
                    ("missing", "Missing"),
                ],
                default="active",
                max_length=16,
            ),
        ),
    ]
