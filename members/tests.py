import datetime
import requests_mock
from django.contrib.auth.hashers import make_password
from django.test import TestCase, override_settings
from . import factories


class LoggedTestMixin(object):
    def setUp(self):
        adhesion = factories.AdhesionFactory.create(person__password=make_password('toto'))
        self.client.login(username=adhesion.person.number, password='toto')
        super().setUp()


class LoginTests(TestCase):
    def test_model(self):
        adhesion = factories.AdhesionFactory.create(person__password=make_password('toto'))
        logged = self.client.login(username=adhesion.person.number, password='toto')
        self.assertTrue(logged)

    @override_settings(NOW=lambda: datetime.datetime(2015, 9, 30))
    def test_model_renewing(self):
        adhesion = factories.AdhesionFactory.create(person__password=make_password('toto'))
        logged = self.client.login(username=adhesion.person.number, password='toto')
        self.assertTrue(logged)

    @override_settings(NOW=lambda: datetime.datetime(2015, 10, 1))
    def test_model_not_renewed(self):
        adhesion = factories.AdhesionFactory.create(person__password=make_password('toto'))
        logged = self.client.login(username=adhesion.person.number, password='toto')
        self.assertFalse(logged)

    @requests_mock.Mocker()
    def test_entrecles(self, mocker):
        mocker.get('http://entrecles.eedf.fr/Default.aspx',
                   text='<input id="__VIEWSTATE" value=""><input id="__EVENTVALIDATION" value="">')
        mocker.post('http://entrecles.eedf.fr/Default.aspx', status_code=302, headers={'Location': '/Accueil.aspx'})
        adhesion = factories.AdhesionFactory.create()
        logged = self.client.login(username=adhesion.person.number, password='toto')
        self.assertTrue(logged)

    @requests_mock.Mocker()
    def test_no_person(self, mocker):
        mocker.get('http://entrecles.eedf.fr/Default.aspx',
                   text='<input id="__VIEWSTATE" value=""><input id="__EVENTVALIDATION" value="">')
        mocker.post('http://entrecles.eedf.fr/Default.aspx', text='')
        logged = self.client.login(username='000000', password='toto')
        self.assertFalse(logged)
