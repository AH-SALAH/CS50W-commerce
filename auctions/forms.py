from django.forms.fields import ChoiceField, BooleanField
from django.forms.widgets import CheckboxInput, DateTimeInput, FileInput, NumberInput, Select, TextInput, Textarea
# from django.urls import reverse
# from django.utils.functional import lazy
from .models import Bid, Category, Comment, Watchlist, Listing
from django.forms import ModelForm, HiddenInput, TextInput, Form
from django.utils.translation import gettext_lazy as _
# from django.utils.timezone import datetime


REQUIRED_CSS_CLASS = 'bold fw-bold form-label'
FORM_CONTROL_CLASS = 'form-control w-100'


class WatchlistForm(ModelForm):
    class Meta:
        model = Watchlist
        fields = ['listing']
        widgets = {'listing': HiddenInput(attrs={"class": "form-control"})}


class ListingForm(ModelForm):

    class Meta:
        model = Listing
        exclude = ['slug', 'last_price', 'user', 'closed', 'winner']
        widgets = {
            'title': TextInput(attrs={"class": FORM_CONTROL_CLASS, "placeholder": _("title")}),
            'desc': Textarea(attrs={"class": FORM_CONTROL_CLASS, "placeholder": _("description")}),
            'price': NumberInput(attrs={"class": FORM_CONTROL_CLASS, "placeholder": _("price"), "min": 0.0}),
            'category': Select(attrs={"class": FORM_CONTROL_CLASS + ' form-select'}),
            'image': FileInput(attrs={"class": FORM_CONTROL_CLASS}),
            'published_date': DateTimeInput(format='%Y-%m-%dT%H:%M:%S', attrs={"class": FORM_CONTROL_CLASS, "type": "datetime-local", "pattern": "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}"}),
            'expiry_date': DateTimeInput(format='%Y-%m-%dT%H:%M:%S', attrs={"class": FORM_CONTROL_CLASS, "type": "datetime-local", "pattern": "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}"}),
            'is_active': CheckboxInput(attrs={"class": "form-check-input mb-2"}),
        }
        localized_fields = ['title',
                            'desc',
                            # 'price',
                            'category',
                            'image',
                            'published_date',
                            'expiry_date',
                            'is_active'
                            ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            parent__isnull=False)
        self.fields['published_date'].localize = True
        self.fields['published_date'].widget.is_localized = True
        self.fields['expiry_date'].localize = True
        self.fields['expiry_date'].widget.is_localized = True
        # self["expiry_date"].field.widget.attrs.update({'min': self["published_date"].value()})
        self.label_suffix = None
        self.prefix = 'listing'
        self.required_css_class = REQUIRED_CSS_CLASS
        self.error_css_class = 'text-danger'

    def remove_labels(self, list=['title', 'desc']):
        "Remove labels"
        for name in self.fields.keys():
            labels_list = list
            try:
                if name in labels_list:
                    self[name].label = None
            except Exception:
                pass

    def as_d(self):
        "Return this form rendered as HTML <div>s."
        # xgettext:no-python-format
        return self._html_output(
            normal_row="""<div%(html_class_attr)s>
                                %(label)s
                                %(field)s
                                %(help_text)s
                            </div>
                        """,
            error_row='%s',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True,
        )


class AddBidForm(ModelForm):
    class Meta:
        model = Bid
        fields = ['amount', 'listing']
        widgets = {
            'amount': NumberInput(attrs={"class": "form-control", "placeholder": _("Place Your Bid"), "min": 0.0, "autofocus": True}),
            'listing': HiddenInput(attrs={"class": "form-control", "name": "bid-listing"}),
        }
        localized_fields = '__all__'

    def __init__(self, ls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = _('Bid')
        self['listing'].field.widget.attrs.update({'value': ls})
        self.label_suffix = None
        self.prefix = 'bid'
        self.required_css_class = REQUIRED_CSS_CLASS
        self.error_css_class = 'text-danger'


class AddCommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ['content', 'listing']
        widgets = {
            'content': Textarea(attrs={"class": "form-control", "placeholder": _("Write a Comment"), "rows": 3}),
            'listing': HiddenInput(attrs={"class": "form-control"}),
        }
        localized_fields = '__all__'

    def __init__(self, ls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = _('Comment')
        self['listing'].field.widget.attrs.update({'value': ls})
        self.label_suffix = None
        self.prefix = 'comment'
        self.required_css_class = REQUIRED_CSS_CLASS
        self.error_css_class = 'text-danger'


class CloseListingForm(ModelForm):

    class Meta:
        model = Listing
        fields = ['closed']
        widgets = {
            'closed': HiddenInput(attrs={"class": "form-control"}),
        }
        localized_fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['closed'].initial = True
        self['closed'].help_text = _(
            'Close this Auction, The last bid user will be the Winner.')
        self.label_suffix = None
        self.required_css_class = REQUIRED_CSS_CLASS
        self.error_css_class = 'text-danger'


class FilterSortForm(Form):
    # reverse_lazy = lazy(reverse, str)

    handle_change = """
        location.search.startsWith('?') ?
            location.search.indexOf(this.name) > -1 ? 
                location.search = 
                (
                    this.value ? 
                    (
                        location.search.replace(
                            new RegExp(this.value.split('=')[0].replace('?', '')+'=.{1}', 'i'), 
                            this.value.replace('?', '')
                        )
                    ) 
                    : 
                    (
                        location.search.match(new RegExp('('+this.name+'=.{1})[&]', 'i')) && 
                            location.search.match(new RegExp('('+this.name+'=.{1})[&]', 'i'))[0].slice(-1) == '&' ?
                            location.search.replace(
                                new RegExp('('+this.name+'=.{1})[&]', 'i'),
                                ''
                            )
                        : 
                        (
                            location.search.match(new RegExp('[?]('+this.name+'=.{1})', 'i')) &&
                            location.search.match(new RegExp('('+this.name+'=.{1})[&]?', 'i'))[0].slice(-1) != '&' ?
                                location.search.replace(
                                    new RegExp('[?]?('+this.name+'=.{1})', 'i'),
                                    ''
                                )
                                : 
                                location.search.replace(
                                    new RegExp('[&|?]?('+this.name+'=.{1})', 'i'),
                                    ''
                                )
                        ) 
                    ) 
                )
                : 
                location.search+=this.value.replace('?', '&') 
            : 
            location.search+=this.value
        """
    handle_check_change = """
        location.search.startsWith('?') ? 
            location.search.indexOf(this.name) > -1 ? 
                location.search = location.search.replace(
                    this.dataset.value.replace('?', '')+'='+ Boolean(JSON.parse(this.value.toLocaleLowerCase())), 
                    this.dataset.value.replace('?', '') +'='+ !Boolean(JSON.parse(this.value.toLocaleLowerCase()))) : 
                location.search+=this.dataset.value.replace('?', '&') +'='+ !Boolean(JSON.parse(this.value.toLocaleLowerCase())) : 
            location.search+=this.dataset.value +'='+ !Boolean(JSON.parse(this.value.toLocaleLowerCase()))
        """

    date = ChoiceField(
        localize=True,
        choices=(
            ("?date=1", _("oldest")),
            ("?date=2", _("newest"))
        ),
        initial="?date=2",
        widget=Select(
            attrs={
                "class": FORM_CONTROL_CLASS+' form-select',
                "onchange": handle_change,
            }
        ),
        label_suffix='',
        label=_('Date'),
        required=False,
    )
    price = ChoiceField(
        localize=True,
        choices=(
            ("?price=1", _("lowest")),
            ("?price=2", _("highest"))
        ),
        initial="?price=2",
        widget=Select(
            attrs={
                "class": FORM_CONTROL_CLASS+' form-select',
                "onchange": handle_change,
            }
        ),
        label_suffix='',
        label=_('Price'),
        required=False,
    )
    closed = BooleanField(
        localize=True,
        initial=False,
        widget=CheckboxInput(
            attrs={
                "class": 'form-check-input',
                "onchange": handle_check_change,
                "datavalue": "?closed",
            }
        ),
        label_suffix='',
        label=_('Closed'),
        required=False,
    )
    exp_s = BooleanField(
        localize=True,
        initial=False,
        widget=CheckboxInput(
            attrs={
                "class": 'form-check-input',
                "onchange": handle_check_change,
                "datavalue": "?exp_s",
            }
        ),
        label_suffix='',
        label=_('Expires in 1 week'),
        required=False,
    )
