from django.test import TestCase
from members.factories import NominationFactory
from .factories import AccountFactory, AnalyticFactory, PurchaseFactory, ThirdPartyFactory, \
    TransactionFactory, YearFactory
from .models import Purchase


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
        purchase = PurchaseFactory.create()
        response = self.client.get('/accounting/{}/purchase/'.format(purchase.year.pk))
        self.assertContains(response, "Achats")
        self.assertContains(response, "Test purchase")

    def test_purchase_detail(self):
        purchase = PurchaseFactory.create()
        response = self.client.get('/accounting/{}/purchase/{}/'.format(purchase.year.pk, purchase.pk))
        self.assertContains(response, "Ventilation")
        self.assertContains(response, "Test purchase")

    def test_purchase_update_get(self):
        purchase = PurchaseFactory.create()
        response = self.client.get('/accounting/{}/purchase/{}/update/'.format(purchase.year.pk, purchase.pk))
        self.assertContains(response, "Modifier l'achat Test purchase")

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
            'transaction_set-INITIAL_FORMS': '1',
            'transaction_set-0-account': AccountFactory.create(prefix=6000000).pk,
            'transaction_set-0-analytic': AnalyticFactory.create().pk,
            'transaction_set-0-expense': '1.42',
            'transaction_set-0-id': TransactionFactory.create(account__prefix=6000000).pk,
        }
        response = self.client.post('/accounting/{}/purchase/create/'.format(year.pk), data)
        self.assertRedirects(response, '/accounting/{}/purchase/'.format(year.pk))
        purchase = Purchase.objects.get()
        self.assertEqual(purchase.title, "Nouvel intitulé")
