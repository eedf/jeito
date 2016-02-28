from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from .utils import first_season, current_season


class AdhesionsForm(forms.Form):
    season_choices = [
        (i, "{}/{}".format(i - 1, i))
        for i in range(current_season(), first_season() - 1, -1)
    ]
    season = forms.ChoiceField(label="Saison", choices=season_choices)
    reference = forms.ChoiceField(label="Référence", choices=[(None, "Année N-1")] + season_choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'season',
            'reference',
            HTML("""<button type="submit" class=\"btn btn-success\">
                    <span class="glyphicon glyphicon-ok-sign"></span> Appliquer
                    </button>"""),
        )
