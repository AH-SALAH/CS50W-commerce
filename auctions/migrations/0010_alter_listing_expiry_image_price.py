# Generated by Django 3.2.7 on 2021-09-12 05:19

import auctions.models
import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0009_alter_listing_expiry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='expiry_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 10, 10, 5, 19, 31, 339416, tzinfo=utc), verbose_name='expiry date'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='image',
            field=models.ImageField(blank=True, default='listing_imgs/default.png', null=True, upload_to=auctions.models.Listing.user_directory_path, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=19, verbose_name='start price'),
        ),
    ]
