# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-31 17:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('branch_code', models.CharField(max_length=12)),
                ('account_number', models.CharField(max_length=8)),
                ('account_holder_name', models.CharField(max_length=100)),
                ('country_code', models.CharField(max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('email', models.CharField(max_length=100)),
                ('given_name', models.CharField(max_length=40)),
                ('family_name', models.CharField(max_length=40)),
                ('address_line1', models.CharField(blank=True, max_length=100, null=True)),
                ('address_line2', models.CharField(blank=True, max_length=100, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country_code', models.CharField(blank=True, max_length=2, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CustomerDataInput',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.CharField(max_length=100)),
                ('given_name', models.CharField(max_length=40)),
                ('family_name', models.CharField(max_length=40)),
                ('address_line1', models.CharField(max_length=100)),
                ('address_line2', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=40)),
                ('postal_code', models.CharField(max_length=10)),
                ('country_code', models.CharField(max_length=2)),
                ('branch_code', models.CharField(max_length=8)),
                ('account_number', models.CharField(max_length=12)),
            ],
        ),
        migrations.CreateModel(
            name='CustomerOrder',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('subscription', models.BooleanField()),
                ('amount', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Mandate',
            fields=[
                ('id', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('scheme', models.CharField(max_length=10)),
                ('linked_bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='example_checkout.BankAccount')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('amount', models.IntegerField(default=0)),
                ('charge_date', models.DateField()),
                ('currency', models.CharField(max_length=3)),
                ('reference', models.CharField(blank=True, max_length=140, null=True)),
                ('status', models.CharField(max_length=50)),
                ('linked_mandate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='example_checkout.Mandate')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=40)),
                ('amount', models.IntegerField(default=0)),
                ('currency', models.CharField(max_length=3)),
                ('day_of_month', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('interval_unit', models.CharField(max_length=40)),
                ('interval', models.IntegerField(default=0)),
                ('start_date', models.DateField()),
                ('status', models.CharField(max_length=40)),
                ('linked_mandate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='example_checkout.Mandate')),
            ],
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='linked_customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='example_checkout.Customer'),
        ),
    ]
