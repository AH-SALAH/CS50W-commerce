from auctions.models import Category, Listing
from django.utils.timezone import now as tz_now

def footer_ctx(request):
    listings = Listing.objects.filter(is_active=True, published_date__lte=tz_now(),
                                         expiry_date__gt=tz_now())[:5]
    categories = Category.objects.all()[:5]

    return {
        "listings": listings,
        "categories": categories
    }