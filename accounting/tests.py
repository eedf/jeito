from django.test import TestCase
from members.factories import NominationFactory
from .factories import AccountFactory, AnalyticFactory, PurchaseFactory, ThirdPartyFactory, YearFactory
from .models import Purchase, Transaction


class LoggedOutViewsTests(TestCase):
    def assertForbid(self, url, method='get'):
        response = getattr(self.client, method)(url)
        self.assertRedirects(response, '/login/?next=' + url)

    def test_purchase_list(self):
        year = YearFactory.create()
        self.assertForbid('/accounting/{}/purchase/'.format(year.pk))

    def test_purchase_detail(self):
        purchase = PurchaseFactory.create()
        self.assertForbid('/accounting/{}/purchase/{}/'.format(purchase.year.pk, purchase.pk))

    def test_purchase_update_get(self):
        purchase = PurchaseFactory.create()
        self.assertForbid('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk))

    def test_purchase_update_post(self):
        purchase = PurchaseFactory.create()
        self.assertForbid('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk), method='post')

    def test_purchase_create_get(self):
        year = YearFactory.create()
        self.assertForbid('/accounting/{}/purchase/create/'.format(year.pk))

    def test_purchase_create_post(self):
        year = YearFactory.create()
        self.assertForbid('/accounting/{}/purchase/create/'.format(year.pk), method='post')


class LoggedInViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nomination = NominationFactory.create(structure__number='2700000500')

    def setUp(self):
        self.client.force_login(user=self.nomination.adhesion.person)

    def test_purchase_list(self):
        year = YearFactory.create(title=2000)
        PurchaseFactory.create(year=year, transactions__amount=1.11)
        PurchaseFactory.create(year=year, transactions__amount=2.22)
        response = self.client.get('/accounting/{}/purchase/'.format(year.pk))
        self.assertContains(response, "Achats 2000")
        self.assertContains(response, "1,11")
        self.assertContains(response, "2,22")
        self.assertContains(response, "3,33")

    def test_purchase_detail(self):
        purchase = PurchaseFactory.create(transactions__amount=1.11)
        response = self.client.get('/accounting/{}/purchase/{}/'.format(purchase.year.pk, purchase.pk))
        self.assertContains(response, "Test purchase")
        self.assertContains(response, "1,11", count=3)

    def test_purchase_update_get(self):
        purchase = PurchaseFactory.create(transactions__amount=1.11)
        response = self.client.get('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk))
        self.assertContains(response, "Modifier l'achat Test purchase")
        self.assertContains(response, 'name="amount" value="1.11"')
        self.assertContains(response, 'name="transaction_set-0-expense" value="1.11"')

    def test_purchase_update_post(self):
        purchase = PurchaseFactory.create()
        data = {
            'title': "Intitulé modifié",
            'date': '2010-06-18',
            'thirdparty': ThirdPartyFactory.create(type=1).pk,
            'amount': '1.42',
            'transaction_set-TOTAL_FORMS': '1',
            'transaction_set-INITIAL_FORMS': '1',
            'transaction_set-0-account': AccountFactory.create(prefix=6000000).pk,
            'transaction_set-0-analytic': AnalyticFactory.create().pk,
            'transaction_set-0-expense': '1.42',
            'transaction_set-0-id': purchase.transaction_set.get(account__number__startswith='6').pk,
        }
        response = self.client.post('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk), data)
        self.assertRedirects(response, '/accounting/{}/purchase/'.format(purchase.year.pk))
        purchase.refresh_from_db()
        self.assertEqual(purchase.title, "Intitulé modifié")

    def test_purchase_update_form_invalid(self):
        purchase = PurchaseFactory.create()
        data = {
            'title': "Intitulé modifié",
            'date': '2010-06-18',
            'thirdparty': ThirdPartyFactory.create(type=1).pk,
            # missing 'amount'
            'transaction_set-TOTAL_FORMS': '1',
            'transaction_set-INITIAL_FORMS': '1',
            'transaction_set-0-account': AccountFactory.create(prefix=6000000).pk,
            'transaction_set-0-analytic': AnalyticFactory.create().pk,
            'transaction_set-0-expense': '1.42',
            'transaction_set-0-id': purchase.transaction_set.get(account__number__startswith='6').pk,
        }
        response = self.client.post('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk), data)
        self.assertContains(response, "Ce champ est obligatoire")

    def test_purchase_update_formset_invalid(self):
        purchase = PurchaseFactory.create()
        data = {
            'title': "Intitulé modifié",
            'date': '2010-06-18',
            'thirdparty': ThirdPartyFactory.create(type=1).pk,
            'amount': '1.42',
            'transaction_set-TOTAL_FORMS': '1',
            'transaction_set-INITIAL_FORMS': '1',
            'transaction_set-0-account': AccountFactory.create(prefix=6000000).pk,
            'transaction_set-0-analytic': AnalyticFactory.create().pk,
            # missing 'transaction_set-0-expense',
            'transaction_set-0-id': purchase.transaction_set.get(account__number__startswith='6').pk,
        }
        response = self.client.post('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk), data)
        self.assertContains(response, "Ce champ est obligatoire")

    def test_purchase_create_get(self):
        year = YearFactory.create()
        response = self.client.get('/accounting/{}/purchase/create/'.format(year.pk))
        self.assertContains(response, "Ajouter un achat")

    def test_purchase_create_post(self):
        year = YearFactory.create()
        data = {
            'title': "Nouvel intitulé",
            'date': '2010-06-18',
            'thirdparty': ThirdPartyFactory.create(type=1).pk,
            'amount': '1.42',
            'transaction_set-TOTAL_FORMS': '1',
            'transaction_set-INITIAL_FORMS': '0',
            'transaction_set-0-account': AccountFactory.create(prefix=6000000).pk,
            'transaction_set-0-analytic': AnalyticFactory.create().pk,
            'transaction_set-0-expense': '1.42',
        }
        response = self.client.post('/accounting/{}/purchase/create/'.format(year.pk), data)
        self.assertRedirects(response, '/accounting/{}/purchase/'.format(year.pk))
        self.assertQuerysetEqual(Purchase.objects.all(), ["<Purchase: Nouvel intitulé>"])
        self.assertQuerysetEqual(
            Transaction.objects.all(),
            ["<Transaction: Nouvel intitulé>", "<Transaction: Nouvel intitulé>"],
            ordered=False
        )
