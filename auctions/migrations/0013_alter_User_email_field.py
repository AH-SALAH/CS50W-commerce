# Generated by Django 3.2.7 on 2021-09-13 00:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0012_alter_listing_expiry_watchlist_listing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=100, null=True, unique=True, verbose_name='email address'),
        ),
    ]
