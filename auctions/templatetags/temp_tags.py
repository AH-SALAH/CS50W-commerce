from django import template

from auctions.models import Listing

register = template.Library()

@register.filter(name='split')
def split(str, key):
    return str.split(key)

@register.simple_tag(name='get_listing_img_url')
def get_listing_img_url(*args, **kwargs):
    return Listing.get_image_url(*args, **kwargs)