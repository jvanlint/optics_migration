# Generated by Django 5.0.3 on 2024-03-27 05:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opticsapp", "0007_alter_dcsairframe_dcsname"),
    ]

    operations = [
        migrations.AlterField(
            model_name="airframe",
            name="dcsname",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="opticsapp.dcsairframe",
            ),
        ),
    ]