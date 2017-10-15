import datetime
import haystack
from django.core.management import call_command
from django.test import TestCase, override_settings
from members.tests import LoggedTestMixin


class HaystackTestCase(TestCase):
    def setUp(self):
        haystack.connections.reload('default')
        super().setUp()

    def tearDown(self):
        call_command('clear_index', interactive=False, verbosity=0)


class LoggedTests(LoggedTestMixin, HaystackTestCase):
    @override_settings(NOW=lambda: datetime.datetime(2015, 1, 1))
    def test_index_view(self):
        response = self.client.get('/docs/')
        self.assertContains(response, '<form method="get" id="docs-search-form">')

    @override_settings(NOW=lambda: datetime.datetime(2015, 1, 1))
    def test_create_view(self):
        response = self.client.get('/docs/create/')
        self.assertContains(response, '<h1>Ajouter un document</h1>')
