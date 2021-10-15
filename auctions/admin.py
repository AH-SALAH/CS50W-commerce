from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Bid, Listing, Category, Comment, Watchlist
from django.contrib.auth.forms import (UserChangeForm, UserCreationForm,)
from django.utils.timezone import now as tz_now


class UserCreationForm(UserCreationForm):
    """A form for creating users.
    """

    class Meta:
        model = get_user_model()
        fields = ('username', 'email')


class UserChangeForm(UserChangeForm):
    """A form for updating users.
    """

    class Meta:
        model = get_user_model()
        fields = '__all__'


@admin.register(get_user_model())
class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
         'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


class CategoryChangeForm(forms.ModelForm):
    """
        customize parent field queryset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Category.objects.filter(
            parent=None).exclude(name=self.instance.name)

    class Meta:
        model = Category
        fields = '__all__'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryChangeForm
    list_display = ('name', 'parent')


class CommentChangeForm(forms.ModelForm):
    """
        customize field queryset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Comment.objects.exclude(
            pk=self.instance.pk)
        self.fields['listing'].queryset = Listing.objects.filter(
            is_active=True, published_date__lte=tz_now(),
            expiry_date__gt=tz_now())

    class Meta:
        model = Comment
        fields = '__all__'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    form = CommentChangeForm
    list_display = ('content', 'parent', 'date', 'is_active')
    list_per_page = 30


class ListingChangeForm(forms.ModelForm):
    """
        customize parent field queryset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().exclude(
            parent=None)

    class Meta:
        model = Listing
        fields = '__all__'


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    form = ListingChangeForm
    list_display = ('title', 'price', 'last_price',
                    'category', 'published_date', 'is_active')
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    filter_horizontal = ('listing',)


class BidChangeForm(forms.ModelForm):
    """
        customize queryset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['listing'].queryset = Listing.objects.filter(
            is_active=True)

    class Meta:
        model = Bid
        fields = '__all__'

    def clean(self):
        super().clean()
        # validate amount
        bid_amount = self.cleaned_data.get('amount')
        form_listing = self.cleaned_data.get('listing')
        listing = {}
        try:
            if form_listing:
                listing = Listing.objects.get(
                    pk=form_listing.pk, is_active=True)
        except Exception as er:
            print('An exception occurred:bidAdmin:er:getting listing', er)
        finally:
            if (listing and listing.price > bid_amount) or (listing and listing.last_price >= bid_amount):
                err_msg = _(
                    'Bid Amount Can\'t be less Than The Listing Price or Less than or Equal to The Latest Bid Amount')
                raise forms.ValidationError({'amount': err_msg})

        return self.cleaned_data


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    '''Admin View for Bid'''

    form = BidChangeForm
    list_display = ('user', 'listing', 'amount', 'date',)
    list_per_page = 30
