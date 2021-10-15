from django.urls import path, re_path
from django.utils.translation import ngettext_lazy as _n, gettext_lazy as _

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path(_("login"), views.login_view, name="login"),
    path(_("logout"), views.logout_view, name="logout"),
    path(_("register"), views.register, name="register"),
    path(_("categories"), views.categories_view, name="categories"),
    path(_("bid/add-bid"), views.add_bid, name="add-bid"),
    path(_("comment/add-comment"), views.add_comment, name="add-comment"),
    re_path(_(r'^categories/(?P<pslug>[\w-]+)/(?P<slug>[\w-]+)?$'),
            views.categories_single_view, name="categories-single"),
    path(_("watchlist/<slug:username>"), views.watchlist, name="watchlist"),
    path(_("listing/add"), views.listing_add_or_edit_view, name="listing-add"),
    re_path(_(r'^categories/(?P<parent_cate>[\w-]+)/(?P<category>[\w-]+)/(?P<slug>[\w-]+)/edit$'),
            views.listing_add_or_edit_view, name="listing-edit"),
    path(_("listings/<slug:username>"), views.my_listings, name="my-listings"),
    re_path(_(r'^categories/(?P<parent_cate>[\w-]+)/(?P<category>[\w-]+)/(?P<slug>[\w-]+)$'),
            views.listing_details, name="listing-details"),
    path(_("lang/<slug:lang>"), views.set_lang, name="set_lang"),
]
