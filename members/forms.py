from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from .utils import first_season, current_season
from .models import Function, Rate


class AdhesionsForm(forms.Form):
    season_choices = [
        (i, "{}/{}".format(i - 1, i))
        for i in range(current_season(), first_season() - 1, -1)
    ]
    sector_choices = (
        (None, 'Tous'),
        (1, 'SLA & régions'),
        (2, 'Services vacances'),
        (3, 'Centres permanents'),
    )
    units_choices = (
        (None, "Toutes"),
        (7, "Lutins"),
        (1, "Louveteaux"),
        (13, "Eclés"),
        (2, "Ainés"),
        (99, "Autres"),
    )
    function_choices = ((None, "Toutes"), ) + Function.CATEGORY_CHOICES
    rate_choices = ((None, "Tous"), ) + Rate.CATEGORY_CHOICES
    season = forms.ChoiceField(label="Saison", choices=season_choices)
    sector = forms.ChoiceField(label="Secteur", choices=sector_choices)
    units = forms.ChoiceField(label="Unités", choices=units_choices)
    function = forms.ChoiceField(label="Fonction", choices=function_choices)
    rate = forms.ChoiceField(label="Tarif", choices=rate_choices)
    # region

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {'id': 'filter'}
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'season',
            'sector',
            'units',
            'function',
            'rate',
        )
