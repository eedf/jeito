from dal import autocomplete
from django import forms
from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = (
            'structure', 'date', 'location', 'nb_presents', 'nb_voters', 'representative', 'favour', 'against',
            'abstention', 'balance', 'budget', 'delegate', 'alternate', 'responsible', 'treasurer',
            'responsible_validation', 'representative_validation', 'comments_activity_report', 'comments_finances',
            'comments_national', 'comments_regional', 'comments_problems',  # 'team',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('representative', 'delegate', 'alternate', 'responsible', 'treasurer'):  # 'team'
            self.fields[name].widget = autocomplete.ModelSelect2(url='members:person_autocomplete')
            self.fields[name].widget.choices = self.fields[name].choices
