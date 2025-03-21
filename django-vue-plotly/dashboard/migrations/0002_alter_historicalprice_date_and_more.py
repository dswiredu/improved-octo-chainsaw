# Generated by Django 5.1 on 2025-03-16 02:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalprice",
            name="date",
            field=models.DateField(db_index=True),
        ),
        migrations.AddIndex(
            model_name="historicalprice",
            index=models.Index(
                fields=["ticker", "date"], name="dashboard_h_ticker__e600ae_idx"
            ),
        ),
    ]
