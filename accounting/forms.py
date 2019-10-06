from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from .models import Account, Analytic, ThirdParty


class PurchaseForm(forms.Form):
    title = forms.CharField(label="Intitulé", max_length=100)
    date = forms.DateField(label="Date")
    provider = forms.ModelChoiceField(label="Fournisseur", queryset=ThirdParty.objects.filter(type=1))
    number = forms.CharField(label="Numéro", max_length=100, required=False)
    deadline = forms.DateField(label="Date limite de paiement", required=False)
    document = forms.FileField(label="Scan PDF", required=False)
    amount = forms.DecimalField(label="Montant total", max_digits=8, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            HTML('<div class="row"><div class="col-md-4">'),
            'amount',
            HTML('</div><div class="col-md-4">'),
            'date',
            HTML('</div><div class="col-md-4">'),
            'document',
            HTML('</div></div>'),
            HTML('<div class="row"><div class="col-md-4">'),
            'provider',
            HTML('</div><div class="col-md-4">'),
            'number',
            HTML('</div><div class="col-md-4">'),
            'deadline',
            HTML('</div></div>'),
        )


class PurchaseTransactionForm(forms.Form):
    account = forms.ModelChoiceField(queryset=Account.objects.filter(number__startswith='6'))
    analytic = forms.ModelChoiceField(queryset=Analytic.objects.all())
    amount = forms.DecimalField(max_digits=8, decimal_places=2)


class PurchaseFormSet(forms.BaseFormSet):
    form = PurchaseTransactionForm
    extra = 3
    can_order = False
    can_delete = False
    max_num = forms.formsets.DEFAULT_MAX_NUM
    validate_max = False
    min_num = forms.formsets.DEFAULT_MIN_NUM
    validate_min = False
    absolute_max = max_num

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            HTML('<div class="row"><div class="col-md-4">'),
            'account',
            HTML('</div><div class="col-md-4">'),
            'analytic',
            HTML('</div><div class="col-md-4">'),
            'amount',
            HTML('</div></div>'),
        )
