# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-31 18:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example_checkout', '0005_auto_20161231_1835'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='day_of_month',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
    ]
