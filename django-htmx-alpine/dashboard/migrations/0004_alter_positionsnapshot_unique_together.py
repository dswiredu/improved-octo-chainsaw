# Generated by Django 5.2.1 on 2025-05-10 21:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_client_instrument_account_positionsnapshot"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="positionsnapshot",
            unique_together=set(),
        ),
    ]
