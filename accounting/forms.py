from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from .models import Account, Journal, PurchaseInvoice, ThirdParty, Transaction


class PurchaseForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Fournisseur", queryset=ThirdParty.objects.filter(type=1))
    revenue = forms.DecimalField(label="Montant total", max_digits=8, decimal_places=2)

    class Meta:
        model = PurchaseInvoice
        fields = ('title', 'date', 'thirdparty', 'number', 'deadline', 'scan', 'revenue')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        purchase = kwargs.get('instance')
        if purchase:
            transaction = purchase.transaction_set.get(account__number='4010000')
            self.fields['thirdparty'].initial = transaction.thirdparty
            self.fields['revenue'].initial = transaction.revenue
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            HTML('<div class="row"><div class="col-md-4">'),
            'revenue',
            HTML('</div><div class="col-md-4">'),
            'date',
            HTML('</div><div class="col-md-4">'),
            'scan',
            HTML('</div></div>'),
            HTML('<div class="row"><div class="col-md-4">'),
            'thirdparty',
            HTML('</div><div class="col-md-4">'),
            'number',
            HTML('</div><div class="col-md-4">'),
            'deadline',
            HTML('</div></div>'),
        )

    def save(self):
        purchase = super().save(commit=False)
        purchase.journal = Journal.objects.get(number="HA")
        purchase.save()
        account = Account.objects.get(number='4010000')
        defaults = {
            'thirdparty': self.cleaned_data['thirdparty'],
            'revenue': self.cleaned_data['revenue'],
        }
        purchase.transaction_set.update_or_create(account=account, defaults=defaults)
        return purchase


class PurchaseTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('account', 'analytic', 'expense')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(number__startswith='6')
        self.fields['analytic'].required = True
        self.fields['expense'].required = True


class PurchaseFormSet(forms.BaseInlineFormSet):
    def __new__(cls, *args, **kwargs):
        formset_class = forms.inlineformset_factory(
            PurchaseInvoice,
            Transaction,
            form=PurchaseTransactionForm,
            can_delete=False,
            extra=3,
        )
        formset = formset_class(
            *args,
            queryset=Transaction.objects.filter(account__number__startswith='6'),
            **kwargs,
        )
        formset.helper = FormHelper()
        formset.helper.form_tag = False
        formset.helper.form_show_labels = False
        formset.helper.layout = Layout(
            HTML('<div class="row"><div class="col-md-4">'),
            'account',
            HTML('</div><div class="col-md-4">'),
            'analytic',
            HTML('</div><div class="col-md-4">'),
            'expense',
            HTML('</div></div>'),
        )
        return formset
