from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.urls import reverse, resolve
from .models import Bid, Comment, Listing, User, Watchlist, Category
from django.core.paginator import Paginator
from django.core import serializers
import json
from .forms import AddBidForm, AddCommentForm, CloseListingForm, ListingForm, FilterSortForm
from django.contrib import messages
from django.utils.translation import ngettext_lazy as _n, gettext as _
from django.utils.html import escape, strip_tags
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.encoding import iri_to_uri
from django.utils.timezone import now as tz_now, timedelta
from django.core.cache import cache
from django.utils import translation


def index(request):

    try:
        # get all categories
        categories = Category.objects.all()
        # get active listings
        active_lists = Listing.objects.filter(
            is_active=True, published_date__lte=tz_now(), expiry_date__gt=tz_now())

        cate_active_lists = active_lists.filter(category__parent__isnull=False)

        user_wl = []
        user_wl_listings = []
        cate_lists = Category.get_category_listings(
            Category, categories=categories, listings=active_lists)

        has_no_parent_cate_list = categories.filter(parent__isnull=True)
        has_parent_cate_list = categories.filter(parent__isnull=False)

        # if user is authenticated, get user related data
        if request.user.is_authenticated:
            user_wl = Watchlist.objects.filter(
                user=request.user).prefetch_related('listing').first()
            user_wl_listings = user_wl.listing.all() if user_wl else []
    except Exception as er:
        print('An exception occurred:index: ', er)

    # if there is a category param, update listings upon
    cate = request.GET.get('cate')

    if cate:
        cate_active_lists = active_lists.filter(
            category__slug=cate)

    # handle sorting & filter
    data = {
        "date": '?date='+request.GET.get('date') if request.GET.get('date') else None,
        "price": '?price='+request.GET.get('price') if request.GET.get('price') else None,
        "closed": '?closed='+request.GET.get('closed') if request.GET.get('closed') else None,
        "exp_s": '?exp_s='+request.GET.get('exp_s') if request.GET.get('exp_s') else None,
    }
    filtered_data = {}

    # change active_lists upon filteration or sorting
    if request.GET.get('date'):
        cate_active_lists = cate_active_lists.order_by(
            'published_date' if request.GET.get('date') == '1' else '-published_date')

    if request.GET.get('price'):
        cate_active_lists = cate_active_lists.order_by(
            'price' if request.GET.get('price') == '1' else '-price')

    if request.GET.get('closed') and request.GET.get('closed').capitalize() == 'True':
        cate_active_lists = cate_active_lists.filter(closed=True)

    if request.GET.get('exp_s') and request.GET.get('exp_s').capitalize() == 'True':
        cate_active_lists = cate_active_lists.filter(
            expiry_date__lt=tz_now() + timedelta(weeks=1))

    # init the form
    sort_form = FilterSortForm(initial=filtered_data if [filtered_data.update({k: data[k].split('=')[
                               1] if k not in ['date', 'price'] else data[k]}) for k in filter((lambda k: data[k]), data)] else {})

    # apply paginator data upon listings (cate_active_lists) data
    paginator = Paginator(cate_active_lists, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = {
        "user_wl_listings": user_wl_listings,
        "has_no_parent_cate_list": has_no_parent_cate_list,
        "has_parent_cate_list": has_parent_cate_list,
        "cate_lists": cate_lists["cate_listing_count"],
        "page_obj": page_obj,
        "paginator": paginator,
        "req_cate": _(cate) if cate else _('All'),  # categories.first().slug
        "ttl_cate_lists": cate_lists["ttl"],
        "sort_form": sort_form,
        "filtered_data": filtered_data,
    }

    return render(request, "auctions/index.html", ctx)


def login_view(request):

    if request.user.is_authenticated:
        return redirect(reverse('index'))

    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)

            try:
                # set user global data in session
                user_listings = Listing.objects.filter(user=user)
                user_listings_count = user_listings.count()
                user_wl = Watchlist.objects.get(user=user)
                user_wl_listings = user_wl.listing.all()
                user_wl_listings_count = user_wl_listings.count()

                request.session['user_listings_count'] = user_listings_count
                request.session['user_wl_listings_count'] = user_wl_listings_count
                request.session['user_wl_listings'] = [l['pk'] for l in json.loads(
                    serializers.serialize('json', user_wl_listings))]
            except Exception as er:
                print('An exception occurred:login: ', er)

            _nxt = cache.get('next')
            if _nxt and url_has_allowed_host_and_scheme(url=_nxt, allowed_hosts=settings.ALLOWED_HOSTS, require_https=request.is_secure()):
                cache.delete('next')
                return HttpResponseRedirect(iri_to_uri(_nxt))

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": _("Invalid username and/or password."),
            })
    else:
        nxt = strip_tags(request.GET.get('next', ''))
        cache.set('next', nxt)

    return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):

    if request.user.is_authenticated:
        return redirect(reverse('index'))

    register_page = "auctions/register.html"

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        if not username or not email:
            return render(request, register_page, {
                "message": _("Email & username shouldn\'t be empty")
            })

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, register_page, {
                "message": _("Passwords must match.")
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError as er:
            return render(request, register_page, {
                "message": er or _("Username already taken.")
            })
        except Exception as er:
            return render(request, register_page, {
                "message": _(er)
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, register_page)


def categories_view(request):
    # get categories
    categories = Category.objects.all()
    # get active listings
    active_lists = Listing.objects.filter(
        is_active=True, published_date__lte=tz_now(), expiry_date__gt=tz_now()).prefetch_related('category', 'category__parent')

    cate_lists = Category.get_category_listings(
        Category, categories, active_lists)

    ctx = {
        "categories": categories,
        "cate_lists": cate_lists.get("cate_listing_count"),
    }

    return render(request, 'auctions/categories.html', ctx)


def categories_single_view(request, pslug='', slug=''):
    # get listing by category
    lists = Listing.objects.filter(
        category__slug=slug or pslug, is_active=True, published_date__lte=tz_now(), expiry_date__gt=tz_now())

    paginator = Paginator(lists, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = {
        "paginator": paginator,
        "lists": lists,
        "page_obj": page_obj,
        "slug": 'categories,categories-single,',
        "var1": _(pslug),
        "var2": _(slug),
    }
    return render(request, 'auctions/categories-single.html', ctx)


@login_required
def watchlist(request, *args, **kwargs):

    if request.method == 'POST':
        listing_id = escape(strip_tags(request.POST.get('listing')))
        nxt = strip_tags(request.POST.get('next'))

        if not listing_id:
            messages.error(request, _('Invalid listing addition'),
                           extra_tags='bg-danger', fail_silently=True)
        else:
            lst = {}
            try:
                # get or create the watchlist then add or remove the m2m listing item
                wl, created = Watchlist.objects.get_or_create(
                    user=request.user)
                # if we found the list then remove it from the wl
                lst = wl.listing.get(pk=listing_id)
                wl.listing.remove(listing_id)
                # xgettext:no-python-format
                messages.success(request, _('%(title)s listing Removed from the watchlist') % {
                                 "title": lst.title}, extra_tags='bg-success', fail_silently=True)
            except Watchlist.DoesNotExist:
                messages.error(request, _('watchlist is not exist'),
                               extra_tags='bg-danger', fail_silently=True)
            except Listing.DoesNotExist:
                # doesn't exist, then add it
                wl.listing.add(listing_id)
                lst = wl.listing.filter(pk=listing_id).first()
                # xgettext:no-python-format
                messages.success(request, _(
                    '%(title)s listing added to the watchlist') % {"title": lst.title}, extra_tags='bg-success', fail_silently=True)

            if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts=settings.ALLOWED_HOSTS, require_https=request.is_secure()):
                return redirect(iri_to_uri(nxt))

    user_wl_listings = []
    try:
        wl = get_object_or_404(Watchlist, user=request.user)
        user_wl_listings = wl.listing.filter(
            is_active=True, published_date__lte=tz_now(), expiry_date__gt=tz_now())
    except Exception as er:
        print('An exception occurred:get_object_or_404:watchlist: ', er)

    paginator = Paginator(user_wl_listings, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    wl_listings_count = request.session.get(
        "user_wl_listings_count") if "user_wl_listings_count" in request.session.keys() else 0

    desc = _n(_('You have %(wl_listings_count)d listing in your Watchlist'),
        _('You have %(wl_listings_count)d listings in your Watchlist'),
        wl_listings_count
    ) % {"wl_listings_count": wl_listings_count}

    ctx = {
        "paginator": paginator,
        "page_obj": page_obj,
        "slug": 'watchlist,',
        "desc": desc,
    }
    return render(request, 'auctions/watchlist.html', ctx)


@login_required
def my_listings(request, *args, **kwargs):
    listings = []
    try:
        listings = get_list_or_404(Listing, user=request.user)
    except Exception as er:
        print('An exception occurred:my-listing', er)

    paginator = Paginator(listings, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    listings_count = request.session.get(
        "user_listings_count") if "user_listings_count" in request.session.keys() else 0

    # xgettext:no-python-format
    desc = _n(
        _('You have %(listings_count)d listing'),
        _('You have %(listings_count)d listings'),
        listings_count
    ) % {"listings_count": listings_count}

    ctx = {
        "paginator": paginator,
        "page_obj": page_obj,
        "slug": 'my listings,',
        "desc": desc,
    }
    return render(request, 'auctions/my-listings.html', ctx)


@login_required
def listing_add_or_edit_view(request, **kwargs):
    obj = {}
    slug = kwargs.get('slug') if kwargs.get('slug') else ''

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)

        if not form.is_valid():
            # print("\n\nreq_post: ", request.POST, "\nfiles: ", request.FILES, "\nfcd: ", form.cleaned_data)
            messages.error(request, _('Invalid listing submission'),
                           extra_tags='bg-danger', fail_silently=True)
        else:
            try:
                obj, created = Listing.objects.update_or_create(
                    user=request.user, slug=slug, defaults=form.cleaned_data)

                if created:
                    # xgettext:no-python-format
                    messages.success(request, _('%(title)s added successfully') % {"title": obj.title},
                                     extra_tags='bg-success', fail_silently=True)

                else:
                    # xgettext:no-python-format
                    messages.success(request, _('%(title)s updated successfully') % {"title": obj.title},
                                     extra_tags='bg-success', fail_silently=True)

            except Listing.MultipleObjectsReturned:
                messages.error(request, _('Sorry, but multiple listing found with the same name, try change others or contact the administrators'),
                               extra_tags='bg-danger', fail_silently=True)

            return redirect(reverse('listing-edit', args=[obj.category.parent.slug, obj.category.slug, obj.slug]) if obj and obj.slug else reverse('my-listings', args=[request.user.username]))

    else:
        if slug:
            obj = Listing.objects.filter(user=request.user, slug=slug).first()
            if obj:
                # # for datetime-local input type representation
                # obj.published_date = obj.published_date.replace(
                #     microsecond=0, tzinfo=None).isoformat()
                # obj.expiry_date = obj.expiry_date.replace(
                #     microsecond=0, tzinfo=None).isoformat()

                form = ListingForm(instance=obj)
            else:
                messages.warning(request, _('No Listing found! Try Adding one!'),
                                 extra_tags='bg-warning', fail_silently=True)

                return redirect(reverse('listing-add'))

        else:
            form = ListingForm()

    listings_count = request.session.get(
        "user_listings_count") if "user_listings_count" in request.session.keys() else 0

    desc = _n(
        _('You have %(listings_count)d listing'),
        _('You have %(listings_count)d listings'),
        listings_count
    ) % {"listings_count": listings_count}

    ctx = {
        "form": form,
        "listing": obj,
        "list_slug": obj.slug if obj and slug else slug,
        "slug": _('Edit listing')+',' if slug else _('Add listing')+',',
        # xgettext:no-python-format
        "desc": desc
    }
    return render(request, 'auctions/edit-modal.html' if slug else 'auctions/listing-add.html', ctx)


def listing_details(request, **kwargs):

    # get the listing for details
    listing = get_object_or_404(
        Listing, category__slug=kwargs.get('category'), slug=kwargs.get('slug'))

    # get related listing
    rel_listing = Listing.objects.filter(category__slug=listing.category.slug, is_active=True, published_date__lte=tz_now(),
                                         expiry_date__gt=tz_now()).exclude(pk=listing.pk).order_by('pk').reverse()[:4]

    # get all comments for this listing
    comments = Comment.objects.filter(
        listing=listing)

    bid_form = AddBidForm(ls=listing.pk)

    # get current tab and comments to show directly if exists
    req_tab = escape(strip_tags(request.GET.get('rt') or ''))
    cmt_edit = escape(strip_tags(request.GET.get('cmt') or ''))

    comments_form = AddCommentForm(ls=listing.pk)

    close_listing_form = CloseListingForm()

    # on post request handle close action
    if request.method == 'POST':

        close_listing_form = CloseListingForm(request.POST)

        if close_listing_form.is_valid():

            # chk if there are any winner and closed status
            if listing.closed and listing.winner:
                messages.error(request, _('The Auction already closed!'),
                               extra_tags='bg-danger', fail_silently=True)
            else:

                try:
                    # chk if there are any bids
                    last_bid = Bid.objects.filter(
                        listing=listing).distinct().first()

                    if not last_bid:
                        messages.error(request, _('Who is The Winner?! No single bid yet!'),
                                       extra_tags='bg-danger', fail_silently=True)
                    else:
                        obj = Listing.objects.filter(pk=listing.pk, user=request.user).update(closed=request.POST.get(
                            'closed'), winner=last_bid.user)

                        if obj:
                            # refresh from db to see refreshed result immediatly
                            listing.refresh_from_db(
                                fields=['winner', 'closed'])
                            # xgettext:no-python-format
                            messages.success(request, _('Auction has been closed, Winner is %(username)s') % {"username": last_bid.user.username},
                                             extra_tags='bg-success', fail_silently=True)

                except Exception as er:
                    print('An exception occurred:close_lisitng', er)

    # pagination for comments
    # paginate on the comments that have no parent [1st lvl]
    paginator = Paginator(comments.filter(parent=None), 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = {
        "listing": listing,
        "comments": comments,
        "close_listing_form": close_listing_form,
        "paginator": paginator,
        "page_obj": page_obj,
        "rel_listing": rel_listing,
        "slug": f'categories,categories-single,listing-details,{listing.title}',
        "var1": _(listing.category.parent.name),
        "var2": _(listing.category.name),
        "var3": _(listing.slug),
        "bid_form": bid_form,
        "comments_form": comments_form,
        "req_tab": req_tab,
        "cmt_edit": cmt_edit,
    }
    return render(request, 'auctions/listing-details.html', ctx)


@login_required
def add_bid(request):
    if request.method == 'POST':

        data = {
            'bid-listing': escape(strip_tags(request.POST.get('listing'))),
            'bid-amount': escape(strip_tags(request.POST.get('bid-amount'))),
            "nxt": '?'+iri_to_uri(request.POST.get('nxt')) if request.POST.get('nxt') else ''
        }
        # get current listing
        listing = Listing.objects.filter(
            pk=data.get('bid-listing')).first()

        # validate eith the form
        form = AddBidForm(ls=listing.pk, data=data)

        if form.is_valid():
            amnt = form.cleaned_data.get('amount')

            # chk if bid is less than listing price or less than or equal the last bid amount
            if amnt <= listing.last_price or amnt < listing.price:
                messages.error(request, _('Bid Amount Can\'t be less Than The Listing Price or Less than or Equal to The Latest Bid Amount'),
                               extra_tags='bg-danger', fail_silently=True)
            else:
                # else add the bid
                try:
                    # create bid obj
                    obj, created = Bid.objects.get_or_create(
                        user=request.user, amount=data.get('bid-amount'), listing=listing)
                    # if bid created
                    if created:
                        # refresh from db to see refreshed result immediatly
                        listing.refresh_from_db(fields=['last_price'])

                        messages.success(request, _('Bid made successfully'),
                                         extra_tags='bg-success', fail_silently=True)
                    else:
                        # else then we found the same bid for the same user & the same amount on the same listing!
                        messages.error(request, _('Bid already made!'),
                                       extra_tags='bg-danger', fail_silently=True)
                except Bid.MultipleObjectsReturned:
                    messages.error(request, _('Multiple Bids Found!'),
                                   extra_tags='bg-danger', fail_silently=True)

        else:
            messages.error(request, _('Bid is not valid'),
                           extra_tags='bg-danger', fail_silently=True)

    return redirect(reverse('listing-details', args=[listing.category.parent.slug, listing.category.slug, listing.slug]) + data.get('nxt') or '')


@login_required
def add_comment(request):
    if request.method == 'POST':

        # get current listing
        listing = Listing.objects.filter(
            pk=request.POST.get('listing')).first()

        data = {
            'comment-listing': escape(strip_tags(request.POST.get('listing'))),
            'comment-content': escape(strip_tags(request.POST.get('comment-content'))),
            'parent': escape(strip_tags(request.POST.get('parent'))) if request.POST.get('parent') else None,
            'edit': escape(strip_tags(request.POST.get('edit'))) if request.POST.get('edit') else 0,
            'nxt': '?'+iri_to_uri(request.POST.get('nxt')) if request.POST.get('nxt') else ''
        }
        # validate with the form
        form = AddCommentForm(data=data, ls=listing.pk)

        if form.is_valid():

            try:
                # if not edit state, then create
                if not data.get('edit'):
                    Comment.objects.create(
                        user=request.user, parent_id=data.get('parent'), **form.cleaned_data)

                    messages.success(request, _('Comment Added successfully'),
                                     extra_tags='bg-success', fail_silently=True)
                else:
                    # if edit state, then get this comment & update it
                    Comment.objects.filter(user=request.user, pk=data.get('edit'), listing=data.get(
                        'comment-listing')).update(content=data.get('comment-content'))

                    messages.success(request, _('Comment Updated successfully'),
                                     extra_tags='bg-success', fail_silently=True)
            except Exception as er:
                print('An exception occurred:add_comment: ', er)

        else:
            # xgettext:no-python-format
            messages.error(request, _(":( %(error)s") % {"error": [f'{escape(strip_tags(k))} - {escape(strip_tags(v))}' for k, v in form.errors.items()][0]},
                           extra_tags='bg-danger', fail_silently=True)

    return redirect(reverse('listing-details', args=[listing.category.parent.slug, listing.category.slug, listing.slug]) + data.get('nxt') or '')


def set_lang(request, lang):

    # get nxt & set default nxt
    nxt_param = request.GET.get('nxt')
    nxt_url = reverse('index')
    # chk nxt param
    if nxt_param and url_has_allowed_host_and_scheme(nxt_param, allowed_hosts=settings.ALLOWED_HOSTS, require_https=request.is_secure()):
        # if so, try to resolve it
        try:
            url_name, args, kwargs = resolve(nxt_param)
            # print("resolve_lang: ", url_name, args, kwargs)
        except Exception as er:
            print('An exception occurred: resolve_er: ', er)
    # change lang
    if lang:
        translation.activate(lang)
        # get the new lang same url
        try:
            nxt_url = reverse(url_name, args=args, kwargs=kwargs)
            # print("reverse_url: ", nxt_url)
        except Exception as er:
            print('An exception occurred: reverse_er: ', er)

    # save the new lang & redirect to the new lang same url
    response = HttpResponse()
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    return redirect(iri_to_uri(_(nxt_url)))
