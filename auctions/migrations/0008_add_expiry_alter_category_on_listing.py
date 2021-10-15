# Generated by Django 3.2.7 on 2021-09-09 18:06

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0007_rename_fields2'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='expiry_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 10, 7, 18, 6, 48, 925154, tzinfo=utc), verbose_name='expiry date'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='category', to='auctions.category', verbose_name='category'),
        ),
    ]
