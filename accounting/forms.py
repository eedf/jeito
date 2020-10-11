from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from django.db.models import Q
from .models import Account, Journal, Purchase, ThirdParty, Transaction, Sale, Income, Expenditure


class PurchaseForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Fournisseur", queryset=ThirdParty.objects.all())
    amount = forms.DecimalField(label="Montant total", max_digits=8, decimal_places=2)

    class Meta:
        model = Purchase
        fields = ('title', 'date', 'thirdparty', 'number', 'deadline', 'scan', 'amount')

    def __init__(self, year, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year
        purchase = kwargs.get('instance')
        if purchase:
            assert purchase.year == year
            assert purchase.journal.number == 'HA'
            self.provider_transaction = purchase.transaction_set.get(account__number__startswith='4')
            self.fields['thirdparty'].initial = self.provider_transaction.thirdparty
            self.fields['amount'].initial = self.provider_transaction.revenue
        else:
            self.provider_transaction = None
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
        purchase.year = self.year
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
        fields = ('account', 'analytic', 'title', 'expense')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(
            Q(number__startswith='6') |
            Q(number__startswith='21')
        )
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
            queryset=Transaction.objects.filter(
                Q(account__number__startswith='6') |
                Q(account__number__startswith='21')
            ),
            **kwargs
        )
        formset.helper = FormHelper()
        formset.helper.form_tag = False
        formset.helper.form_show_labels = False
        formset.helper.layout = Layout(
            HTML('<div class="row"><div class="col-md-4">'),
            'account',
            HTML('</div><div class="col-md-3">'),
            'analytic',
            HTML('</div><div class="col-md-3">'),
            'title',
            HTML('</div><div class="col-md-2">'),
            'expense',
            HTML('</div></div>'),
        )
        return formset


class SaleForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Client", queryset=ThirdParty.objects.all())
    amount = forms.DecimalField(label="Montant total", max_digits=8, decimal_places=2)
    deposit = forms.DecimalField(label="Avance versée", max_digits=8, decimal_places=2, initial=0)

    class Meta:
        model = Sale
        fields = ('title', 'date', 'thirdparty', 'number', 'scan', 'amount')

    def __init__(self, year, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year
        sale = kwargs.get('instance')
        if sale:
            assert self.year == year
            assert sale.journal.number == 'VT'
            try:
                self.deposit_transaction = sale.transaction_set.get(account__number='4190000')
                self.fields['deposit'].initial = self.deposit_transaction.expense
            except Transaction.DoesNotExist:
                self.deposit_transaction = None
            self.client_transaction = sale.transaction_set \
                .get(account__number__in=('4110000', '4500000', '4670000'))
            self.fields['thirdparty'].initial = self.client_transaction.thirdparty
            self.fields['amount'].initial = self.client_transaction.expense
            if self.deposit_transaction:
                self.fields['amount'].initial += self.deposit_transaction.expense
        else:
            self.deposit_transaction = None
            self.client_transaction = None
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

        # Save sale entry
        sale = super().save(commit=False)
        sale.year = self.year
        sale.journal = Journal.objects.get(number="VT")
        sale.save()

        # Save client transaction
        expense = amount - deposit
        if expense != 0:
            if not self.client_transaction:
                self.client_transaction = Transaction(entry=self.instance, account=thirdparty.account)
            self.client_transaction.thirdparty = thirdparty
            self.client_transaction.expense = expense
            self.client_transaction.save()
        else:
            if self.client_transaction:
                self.client_transaction.delete()

        # Save deposit transaction
        if deposit != 0:
            if not self.deposit_transaction:
                account = Account.objects.get(number='4190000')
                self.deposit_transaction = Transaction(entry=self.instance, account=account)
            self.deposit_transaction.thirdparty = thirdparty
            self.deposit_transaction.expense = deposit
            self.deposit_transaction.save()
        else:
            if self.deposit_transaction:
                self.deposit_transaction.delete()

        return sale


class SaleTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('account', 'analytic', 'title', 'revenue')

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
            HTML('</div><div class="col-md-3">'),
            'analytic',
            HTML('</div><div class="col-md-3">'),
            'title',
            HTML('</div><div class="col-md-2">'),
            'revenue',
            HTML('</div></div>'),
        )
        return formset


class IncomeForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Client", queryset=ThirdParty.objects.all())
    amount = forms.DecimalField(label="Montant", max_digits=8, decimal_places=2)
    method = forms.ChoiceField(label="Moyen de paiement", choices=Income.METHOD_CHOICES)
    deposit = forms.BooleanField(label="Avance", required=False)

    class Meta:
        model = Income
        fields = ('title', 'date', 'thirdparty', 'scan', 'amount', 'method', 'deposit')

    def __init__(self, year, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year
        income = kwargs.get('instance')
        if income:
            assert self.year == year
            assert income.journal.number in ('BQ', 'CA')
            self.fields['deposit'].initial = income.deposit
            if income.client_transaction:
                self.fields['thirdparty'].initial = income.client_transaction.thirdparty
                self.fields['amount'].initial = income.client_transaction.revenue
            if income.cash_transaction:
                self.fields['method'].initial = income.cash_transaction.account.number
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
            'method',
            HTML('</div><div class="col-md-4">'),
            'deposit',
            HTML('</div></div>'),
        )

    def save(self):
        # Get values
        thirdparty = self.cleaned_data['thirdparty']
        amount = self.cleaned_data['amount']
        deposit = self.cleaned_data['deposit']
        method = self.cleaned_data['method']

        # Save income entry
        income = super().save(commit=False)
        income.year = self.year
        income.journal = Journal.objects.get(number="CA" if method == '5300000' else 'BQ')
        income.save()

        # Save client transaction
        client_transaction = self.instance.client_transaction or Transaction(entry=self.instance)
        client_transaction.account = Account.objects.get(number='4190000') if deposit else thirdparty.account
        client_transaction.thirdparty = thirdparty
        client_transaction.revenue = amount
        client_transaction.save()

        # Save cash transaction
        cash_transaction = self.instance.cash_transaction or Transaction(entry=self.instance)
        cash_transaction.account = Account.objects.get(number=method)
        cash_transaction.expense = amount
        cash_transaction.save()

        return income


class ExpenditureForm(forms.ModelForm):
    method = forms.ChoiceField(label="Moyen de paiement", choices=Expenditure.METHOD_CHOICES)

    class Meta:
        model = Expenditure
        fields = ('title', 'date', 'scan', 'method')

    def __init__(self, year, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year
        expenditure = kwargs.get('instance')
        if expenditure:
            assert self.year == year
            assert expenditure.journal.number in ('BQ', 'CA')
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            HTML('<div class="row"><div class="col-md-4">'),
            'date',
            HTML('</div><div class="col-md-4">'),
            'method',
            HTML('</div><div class="col-md-4">'),
            'scan',
            HTML('</div></div>'),
        )

    def save(self, formset):
        # Save expenditure entry
        expenditure = super().save(commit=False)
        expenditure.year = self.year
        expenditure.journal = Journal.objects.get(number="CA" if expenditure.method == 3 else 'BQ')
        expenditure.save()

        # Save cash transaction
        cash_transaction = self.instance.cash_transaction or Transaction(entry=self.instance)
        cash_transaction.account = Account.objects.get(number='5300000' if expenditure.method == 3 else '5120000')
        cash_transaction.revenue = sum([form.cleaned_data['expense'] for form in formset if form.cleaned_data])
        cash_transaction.save()

        return expenditure


class ExpenditureTransactionForm(forms.ModelForm):
    thirdparty = forms.ModelChoiceField(label="Fournisseur", queryset=ThirdParty.objects.all())
    deposit = forms.BooleanField(label="Avance", required=False)

    class Meta:
        model = Transaction
        fields = ('thirdparty', 'title', 'expense', 'deposit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['deposit'].initial = self.instance.account.number == '4090000'
        except Account.DoesNotExist:
            self.fields['deposit'].initial = False

    def save(self, commit=True):
        transaction = super().save(commit=False)
        if self.cleaned_data['deposit']:
            transaction.account = Account.objects.get(number='4090000')
        else:
            transaction.account = transaction.thirdparty.account
        if commit:
            transaction.save()
        return transaction


class ExpenditureFormSet(forms.BaseInlineFormSet):
    def __new__(cls, *args, **kwargs):
        formset_class = forms.inlineformset_factory(
            Expenditure,
            Transaction,
            form=ExpenditureTransactionForm,
            can_delete=False,
            extra=3,
        )
        formset = formset_class(
            *args,
            queryset=Transaction.objects.filter(account__number__startswith='4'),
            **kwargs
        )
        formset.helper = FormHelper()
        formset.helper.form_tag = False
        formset.helper.form_show_labels = False
        formset.helper.layout = Layout(
            HTML('<div class="row"><div class="col-md-4">'),
            'thirdparty',
            HTML('</div><div class="col-md-4">'),
            'title',
            HTML('</div><div class="col-md-2">'),
            'deposit',
            HTML('</div><div class="col-md-2">'),
            'expense',
            HTML('</div></div>'),
        )
        return formset


class ThirdPartyForm(forms.ModelForm):
    class Meta:
        model = ThirdParty
        fields = ('number', 'title', 'iban', 'bic', 'client_number', 'account', 'type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            HTML('<div class="row"><div class="col-md-6">'),
            'type',
            HTML('</div><div class="col-md-6">'),
            'account',
            HTML('</div></div>'),
            HTML('<div class="row"><div class="col-md-6">'),
            'number',
            HTML('</div><div class="col-md-6">'),
            'client_number',
            HTML('</div></div>'),
            HTML('<div class="row"><div class="col-md-6">'),
            'iban',
            HTML('</div><div class="col-md-6">'),
            'bic',
            HTML('</div></div>'),
        )
