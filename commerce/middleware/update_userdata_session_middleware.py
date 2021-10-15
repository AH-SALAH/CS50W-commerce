from django.db.models import Prefetch
from auctions.models import Listing
from django.utils.timezone import now as tz_now


class SessionUserDataUpdateMiddleware(object):
    """ middleware that update the session """

    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):

        try:
            # deactivate all expired listings
            Listing.objects.filter(
                expiry_date__lte=tz_now()).update(is_active=False)
        except Exception:
            pass

        # get listings & watchlist data for this usr
        try:
            if request.user.is_authenticated:
                from auctions.models import Watchlist

                wl = Watchlist.objects.filter(user=request.user).prefetch_related(Prefetch(
                    'listing', queryset=Listing.objects.filter(is_active=True, published_date__lte=tz_now(), expiry_date__gt=tz_now())))
                ul = Listing.objects.filter(
                    user=request.user).count()

                if wl:
                    from django.core import serializers
                    import json
                    request.session["user_wl_listings"] = [l['pk'] for l in json.loads(
                        serializers.serialize('json', wl[0].listing.filter(is_active=True)))]
                    request.session["user_wl_listings_count"] = wl[0].listing.count()
                if ul:
                    request.session["user_listings_count"] = ul

                # request.session.save()

        except Exception:
            pass
            # print("mw:er: ", er)
