# Generated by Django 5.2.1 on 2025-05-22 03:27

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SDACurveInputs",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uploaded_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("security_file", models.FileField(upload_to="sda_inputs/security/")),
                ("curve_file", models.FileField(upload_to="sda_inputs/curves/")),
                ("psa", models.FloatField()),
                ("sda", models.FloatField()),
                ("success", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
            ],
        ),
    ]
