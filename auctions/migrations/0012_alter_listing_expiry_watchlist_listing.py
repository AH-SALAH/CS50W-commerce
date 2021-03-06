# Generated by Django 3.2.7 on 2021-09-12 22:35

import auctions.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0011_alter_listing_expiry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='expiry_date',
            field=models.DateTimeField(default=auctions.models.Listing.default_expiry_date, verbose_name='expiry date'),
        ),
        migrations.AlterField(
            model_name='watchlist',
            name='listing',
            field=models.ManyToManyField(blank=True, related_name='watchlist_listing', to='auctions.Listing', verbose_name='listing'),
        ),
    ]
