from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Submit
from django import forms
from django.conf import settings
from members.models import Structure
from .models import Booking, BookingState


# TODO: add a reinit button
# TODO: use https://behigh.github.io/bootstrap_dropdowns_enhancement
class BookingFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = settings.NOW().year
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.form_action = 'booking:booking_list'
        self.helper.layout = Layout(
            'structure',
            'year',
            'month',
            'org_type',
            InlineCheckboxes('state'),
        )


class BookingItemFilterForm(BookingFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_action = 'booking:occupancy'


class StatsFilterForm(BookingFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_action = 'booking:stats'


class CotisationsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = settings.NOW().year
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.form_action = 'booking:cotisations'
        self.helper.layout = Layout(
            'structure',
            'year',
            'org_type',
            InlineCheckboxes('state'),
        )


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('structure', 'title', 'org_type', 'contact', 'email', 'tel', 'state', 'description')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        structures = Structure.objects.centers().for_user(user).order_by('name')
        user_structure = user.adhesion and user.adhesion.structure
        if user_structure in structures:
            kwargs['initial']['structure'] = user_structure
        kwargs['initial']['state'] = BookingState.objects.get(title='Contact')
        super().__init__(*args, **kwargs)
        self.fields['structure'].queryset = structures
        self.fields['structure'].label = "Centre"
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<div class="row"><div class="col-md-6">'),
            'title',
            'structure',
            'description',
            HTML('</div><div class="col-md-6">'),
            'state',
            'org_type',
            'contact',
            'email',
            'tel',
            HTML('</div></div>'),
            Submit('create', 'Ajouter'),
        )
