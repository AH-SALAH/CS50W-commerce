from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now as tz_now
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from util.util import resize_img
from datetime import timedelta
from functools import reduce
from commerce.settings import MEDIA_URL


class User(AbstractUser):
    phone = models.CharField(_('phone'), max_length=11,
                             blank=True, null=True, unique=True)
    email = models.EmailField(
        _('email address'), max_length=100, null=True, unique=True)


class Listing(models.Model):

    def user_directory_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/user_<id>/Y/m/d/listing_imgs/<filename>
        return f'user_{instance.user.pk}/{tz_now().year}/{tz_now().month}/{tz_now().day}/listing_imgs/{filename}'

    def default_expiry_date():
        return tz_now() + timedelta(weeks=4)

    title = models.CharField(_('title'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=70,
                            allow_unicode=True, null=True, blank=True)
    desc = models.TextField(_('description'))
    price = models.DecimalField(
        _('start price'), max_digits=19, decimal_places=2, default=00.00)
    last_price = models.DecimalField(
        _('last price'), max_digits=19, decimal_places=2, default=price.get_default(), null=True, blank=True)
    user = models.ForeignKey(get_user_model(), verbose_name=_('author'),
                             on_delete=models.CASCADE, related_name='author')
    category = models.ForeignKey('category', verbose_name=_('category'), on_delete=models.RESTRICT,
                                 related_name='listing_category')
    image = models.ImageField(
        _('image'), upload_to=user_directory_path, null=True, blank=True)
    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modify_date = models.DateTimeField(
        _('last modified'), auto_now=True)
    published_date = models.DateTimeField(_('published date'), default=tz_now)
    expiry_date = models.DateTimeField(
        _('expiry date'), default=default_expiry_date)
    is_active = models.BooleanField(_('is active'), default=True)
    closed = models.BooleanField(_('closed'), default=False)
    winner = models.ForeignKey(get_user_model(), verbose_name=_('winner'),
                               on_delete=models.DO_NOTHING, null=True, blank=True, related_name='winner')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Listing')
        verbose_name_plural = _('Listings')
        ordering = ('-published_date', )

    def get_absolute_url(self):
        # You may wish to use the django.utils.encoding.iri_to_uri() function
        # to help if you are using strings containing characters outside the ASCII range.
        return reverse('listing-details', kwargs={'parent_cate': self.category.parent or self.category, 'category': self.category, 'slug': self.slug})

    def is_new(self):
        return (self.published_date + ((self.expiry_date - self.published_date) / 3)) > tz_now() and tz_now() < self.expiry_date

    def is_expired(self):
        return tz_now() >= self.expiry_date

    def will_expire_soon(self):
        return (self.expiry_date - ((self.expiry_date - self.published_date) / 3)) < tz_now() and tz_now() < self.expiry_date

    def deactivate_if_expired(self):
        if self.is_expired():
            self.is_active = False

    def set_expiry_date_gt_published(self):
        if self.expiry_date <= self.published_date:
            self.expiry_date = self.published_date + timedelta(weeks=1)

    def is_closed(self):
        return self.closed

    def get_image_url(self, old_img=None):
        if old_img and not self.image:
            self.image = old_img
            return self.image.url
        return self.image.url if self.image else MEDIA_URL+'default.png'

    def save(self, *args, **kwargs):
        # slugify title
        if not self.slug or self.slug != slugify(self.title, allow_unicode=True):
            self.slug = slugify(self.title, allow_unicode=True)

        if self.image:
            # resizing z img
            self.image = resize_img(self.image)

        # correct expiry date if needed
        self.set_expiry_date_gt_published()

        super().save(*args, **kwargs)


class Bid(models.Model):
    user = models.ForeignKey(get_user_model(), verbose_name=_('user'),
                             on_delete=models.CASCADE, related_name='bid_user')
    listing = models.ForeignKey(
        Listing, verbose_name=_('listing'), on_delete=models.CASCADE, related_name='bid_listing')
    amount = models.DecimalField(
        _('bid amount'), max_digits=19, decimal_places=2, default=00.00)
    date = models.DateTimeField(_('date'), default=tz_now)

    def __str__(self):
        return f'{self.user.username} - {self.listing.title}'

    class Meta:
        verbose_name = _('Bid')
        verbose_name_plural = _('Bids')
        ordering = ('-date',)

    def get_absolute_url(self):
        return reverse('bids', kwargs={'username': self.user.username})


class Category(models.Model):
    name = models.CharField(_('name'), max_length=50)
    slug = models.SlugField(_('slug'), max_length=50,
                            allow_unicode=True, null=True, blank=True)
    desc = models.TextField(_('description'))
    parent = models.ForeignKey(
        'self', verbose_name=_('parent category'), limit_choices_to={'parent__isnull': True}, on_delete=models.RESTRICT, null=True, blank=True, related_name='parent_category')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def get_absolute_url(self):
        kwargs = {'pslug': self.parent.slug,
                  'slug': self.slug} if self.parent else {'pslug': self.slug}
        return reverse('categories-single', kwargs=kwargs)

    def save(self, *args, **kwargs):
        # slugify name
        if not self.slug or self.slug != slugify(self.name, allow_unicode=True):
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_category_listings(self, categories, listings):
        """chk how many listings in this category

        Args:
            categories (Category): Category instance
            listings (Listing): Listing instance

        Returns:
            Dict: Dict of [{category__Pk: <int:How many Listings>},..]
        """
        if not categories and not listings:
            return {}

        # chk how many listings in this category
        cate_listing_count = []
        ttl = 0
        for c in categories:
            for b in listings:
                if b.category.pk == c.pk:
                    # 1st loop arr is empty, so chk if there are values in arr, else append new
                    if cate_listing_count:
                        # if not empty, find the k & update, else append new
                        for obj in cate_listing_count:
                            if c.pk in obj:
                                obj.update({c.pk: obj[c.pk]+1})
                                break
                        else:
                            cate_listing_count.append({c.pk: 1})
                    else:
                        cate_listing_count.append({c.pk: 1})

        # get ttl values
        ttl = reduce(lambda a, b: a+b, [list(k.values())[0]
                     for k in cate_listing_count])

        return {"cate_listing_count": cate_listing_count, "ttl": ttl}


class Comment(models.Model):
    content = models.TextField(_('content'))
    date = models.DateTimeField(_('date'), default=tz_now)
    user = models.ForeignKey(
        get_user_model(), verbose_name=_('user'), on_delete=models.CASCADE, related_name='comment_user')
    listing = models.ForeignKey(
        Listing, verbose_name=_('listing'), on_delete=models.CASCADE, related_name='comment_listing')
    parent = models.ForeignKey(
        'self', verbose_name=_('reply on'), on_delete=models.RESTRICT, null=True, blank=True, related_name='parent_comment')
    is_active = models.BooleanField(_('is active'), default=True)

    def __str__(self):
        return f'{self.content[:20]}... ({self.user.username})'

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ('date', )


class Watchlist(models.Model):
    user = models.OneToOneField(
        get_user_model(), verbose_name=_('watchlist user'), on_delete=models.CASCADE, related_name='watchlist_user')
    listing = models.ManyToManyField(
        Listing, verbose_name=_('listing'), related_name='watchlist_listing', blank=True)

    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        verbose_name = _('Watchlist')
        verbose_name_plural = _('Watchlists')

    def get_absolute_url(self):
        return reverse('watchlist', kwargs={'username': self.user.username})
