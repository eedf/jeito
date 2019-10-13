from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from .models import Account, Journal, Purchase, ThirdParty, Transaction, Sale


class PurchaseForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Fournisseur", queryset=ThirdParty.objects.filter(type=1))
    amount = forms.DecimalField(label="Montant total", max_digits=8, decimal_places=2)

    class Meta:
        model = Purchase
        fields = ('title', 'date', 'thirdparty', 'number', 'deadline', 'scan', 'amount')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        purchase = kwargs.get('instance')
        if purchase:
            assert purchase.journal.number == 'HA'
            self.provider_transaction = purchase.transaction_set.get(account__number__startswith='4')
            self.fields['thirdparty'].initial = self.provider_transaction.thirdparty
            self.fields['amount'].initial = self.provider_transaction.revenue
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            HTML('<div class="row"><div class="col-md-4">'),
            'amount',
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
        # Get values
        thirdparty = self.cleaned_data['thirdparty']
        amount = self.cleaned_data['amount']

        # Save purchase entry
        purchase = super().save(commit=False)
        purchase.journal = Journal.objects.get(number="HA")
        purchase.save()

        # Save provider transaction
        if not self.provider_transaction:
            self.provider_transaction = Transaction(entry=self.instance, account=thirdparty.account)
        self.provider_transaction.thirdparty = thirdparty
        self.provider_transaction.revenue = amount
        self.provider_transaction.save()

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
            Purchase,
            Transaction,
            form=PurchaseTransactionForm,
            can_delete=False,
            extra=3,
        )
        formset = formset_class(
            *args,
            queryset=Transaction.objects.filter(account__number__startswith='6'),
            **kwargs
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


class SaleForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Client", queryset=ThirdParty.objects.filter(type=0))
    amount = forms.DecimalField(label="Montant total", max_digits=8, decimal_places=2)
    deposit = forms.DecimalField(label="Acompte versé", max_digits=8, decimal_places=2, required=False)

    class Meta:
        model = Sale
        fields = ('title', 'date', 'thirdparty', 'number', 'scan', 'amount')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        purchase = kwargs.get('instance')
        if purchase:
            assert purchase.journal.number == 'VT'
            try:
                self.deposit_transaction = purchase.transaction_set.get(account__number='4190000')
                self.fields['deposit'].initial = self.deposit_transaction.expense
            except Transaction.DoesNotExist:
                self.deposit_transaction = None
            self.client_transaction = purchase.transaction_set \
                .get(account__number__in=('4110000', '4500000', '4670000'))
            self.fields['thirdparty'].initial = self.client_transaction.thirdparty
            self.fields['amount'].initial = self.client_transaction.expense + self.deposit_transaction.expense
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            HTML('<div class="row"><div class="col-md-4">'),
            'amount',
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
            'deposit',
            HTML('</div></div>'),
        )

    def save(self):
        # Get values
        thirdparty = self.cleaned_data['thirdparty']
        amount = self.cleaned_data['amount']
        deposit = self.cleaned_data['deposit']

        # Save purchase entry
        purchase = super().save(commit=False)
        purchase.journal = Journal.objects.get(number="VT")
        purchase.save()

        # Save client transaction
        if not self.client_transaction:
            self.client_transaction = Transaction(entry=self.instance, account=thirdparty.account)
        self.client_transaction.thirdparty = thirdparty
        self.client_transaction.expense = amount - deposit
        self.client_transaction.save()

        # Save deposit transaction
        if deposit:
            if not self.deposit_transaction:
                account = Account.objects.get(number='4190000')
                self.deposit_transaction = Transaction(entry=self.instance, account=account)
            self.deposit_transaction.thirdparty = thirdparty
            self.deposit_transaction.expense = deposit
            self.deposit_transaction.save()
        else:
            if self.deposit_transaction:
                self.deposit_transaction.delete()
        return purchase


class SaleTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('account', 'analytic', 'revenue')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(number__startswith='7')
        self.fields['analytic'].required = True
        self.fields['revenue'].required = True


class SaleFormSet(forms.BaseInlineFormSet):
    def __new__(cls, *args, **kwargs):
        formset_class = forms.inlineformset_factory(
            Purchase,
            Transaction,
            form=SaleTransactionForm,
            can_delete=False,
            extra=3,
        )
        formset = formset_class(
            *args,
            queryset=Transaction.objects.filter(account__number__startswith='7'),
            **kwargs
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
            'revenue',
            HTML('</div></div>'),
        )
        return formset
