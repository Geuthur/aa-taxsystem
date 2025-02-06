# Generated by Django 4.2.11 on 2025-02-06 11:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("eveonline", "0017_alliance_and_corp_names_are_not_unique"),
        ("authentication", "0024_alter_userprofile_language"),
    ]

    operations = [
        migrations.CreateModel(
            name="General",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "permissions": (
                    ("basic_access", "Can access this app"),
                    ("manage_access", "Can manage Tax System"),
                    ("create_access", "Can add Corporation"),
                ),
                "managed": False,
                "default_permissions": (),
            },
        ),
        migrations.CreateModel(
            name="Members",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("status", models.CharField(blank=True, max_length=50, null=True)),
                ("active", models.BooleanField(default=False)),
                ("payment_notification", models.BooleanField(default=False)),
                ("notice", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Tax Member System",
                "verbose_name_plural": "Tax Member Systems",
                "default_permissions": (),
            },
        ),
        migrations.CreateModel(
            name="Payments",
            fields=[
                ("name", models.CharField(max_length=100)),
                ("context_id", models.AutoField(primary_key=True, serialize=False)),
                ("date", models.DateTimeField(auto_now_add=True, null=True)),
                ("amount", models.DecimalField(decimal_places=0, max_digits=12)),
                (
                    "payment_status",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("payment_date", models.DateTimeField(blank=True, null=True)),
                ("approved", models.BooleanField(default=False)),
                (
                    "payment_member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="member_payment",
                        to="taxsystem.members",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tax Payments",
                "verbose_name_plural": "Tax Payments",
                "default_permissions": (),
            },
        ),
        migrations.CreateModel(
            name="OwnerAudit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("active", models.BooleanField(default=False)),
                ("last_update_wallet", models.DateTimeField(blank=True, null=True)),
                (
                    "alliance",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alliance",
                        to="eveonline.eveallianceinfo",
                    ),
                ),
                (
                    "corporation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="corporation",
                        to="eveonline.evecorporationinfo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tax System Audit",
                "verbose_name_plural": "Tax System Audits",
                "default_permissions": (),
            },
        ),
        migrations.AddField(
            model_name="members",
            name="audit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="audit",
                to="taxsystem.owneraudit",
            ),
        ),
        migrations.AddField(
            model_name="members",
            name="member",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="member",
                to="authentication.userprofile",
            ),
        ),
    ]
