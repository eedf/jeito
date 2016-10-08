from lxml import html
import requests

from django.contrib.auth.backends import ModelBackend

from members.models import Person


class PersonBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        username = username.zfill(6)
        person = super().authenticate(username, password)
        if person:
            return person
        try:
            person = Person.objects.get_by_natural_key(username)
        except Person.DoesNotExist:
            return None
        session = requests.Session()
        response = session.get('http://entrecles.eedf.fr/Default.aspx')
        tree = html.fromstring(response.text)
        params = {
            '__VIEWSTATE': tree.get_element_by_id('__VIEWSTATE').value,
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': tree.get_element_by_id('__EVENTVALIDATION').value,
            'ctl00$MainContent$login': username,
            'ctl00$MainContent$password': password,
            'ctl00$MainContent$_btnValider': 'Se connecter',
        }
        response = session.post('http://entrecles.eedf.fr/Default.aspx',
                                params, allow_redirects=False)
        if response.status_code != requests.codes.found:
            return None
        if response.headers.get('Location') != '/Accueil.aspx':
            return None
        return person
