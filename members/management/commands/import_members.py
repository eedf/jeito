# -*- coding: utf8 -*-

import datetime
import lxml.html
import os
import re
import requests
from html import unescape

from django.core.management.base import BaseCommand, CommandError

from members.models import Structure, Function, Rate, Person, Adhesion


HOST = os.getenv('ENTRECLES_HOST')
BASEURL = 'http://{host}/'.format(host=HOST)
LOGIN = os.getenv('ENTRECLES_LOGIN')
PASSWORD = os.getenv('ENTRECLES_PASSWORD')
FONCTION = os.getenv('ENTRECLES_FUNCTION')
STRUCTURE = os.getenv('ENTRECLES_STRUCTURE')
today = datetime.date.today()
SEASON = os.getenv('ENTRECLES_SEASON', today.year if today.month <= 9 else today.year + 1)


class Command(BaseCommand):
    help = 'Import members'
    tree = None

    def add_arguments(self, parser):
        parser.add_argument('-s', '--update-structures', action='store_true')

    def get(self, url):
        self.stdout.write('GET ' + BASEURL + url)
        self.response = self.session.get(BASEURL + url)
        self.tree = lxml.html.fromstring(self.response.text)

    def post(self, url, params, event_validation=False, **kwargs):
        params['__VIEWSTATE'] = self.tree.get_element_by_id('__VIEWSTATE').value
        params['__VIEWSTATEENCRYPTED'] = ''
        if event_validation:
            params['__EVENTVALIDATION'] = self.tree.get_element_by_id('__EVENTVALIDATION').value
        if not url.startswith('http://'):
            url = BASEURL + url
        self.stdout.write('POST ' + url)
        self.response = self.session.post(url, data=params, **kwargs)
        if kwargs.get('stream'):
            self.tree = None
        else:
            self.tree = lxml.html.fromstring(self.response.text)

    def extract_line(self, cols):
        if cols[1] == "Individu.CodeAdherent":
            return
        if cols[1] in ("eedfadmin", "supradmin"):  # Admin
            return
        if cols[39] != "0":  # Adhésion
            return
        self.nb += 1
        try:
            structure = Structure.objects.get(number=cols[4])
        except Structure.DoesNotExist:
            structure = self.get_structure(cols[4], parent=None, recursive=False)
        try:
            function, created = Function.objects.update_or_create(
                code=cols[6],
                season=SEASON,
                defaults={
                    'name_m': cols[8],
                    'name_f': cols[9],
                }
            )
            rate, created = Rate.objects.get_or_create(
                name=cols[40],
                season=SEASON
            )
            person, created = Person.objects.update_or_create(
                number=cols[1],
                defaults={
                    'gender': Person.GENDER_MALE if cols[0] == "M" else Person.GENDER_FEMALE,
                    'last_name': cols[2],
                    'first_name': cols[3],
                    'email': cols[24],
                }
            )
            if cols[39] == "0":
                adhesion, created = Adhesion.objects.update_or_create(
                    person=person,
                    season=SEASON,
                    defaults={
                        'structure': structure,
                        'function': function,
                        'date': datetime.date(int(cols[37][6:10]), int(cols[37][3:5]), int(cols[37][0:2])),
                        'rate': rate,
                    }
                )
        except:
            self.stdout.write("failed to create {}".format(cols))
            raise

    def extract(self, f, length):
        current = b''
        done = 0
        self.nb = 0
        percent = 0
        row = re.compile(b'<tr><td.*?>(.*?)</td></tr>(.*)$')
        col = re.compile(b'</td><td.*?>')
        while True:
            new = f.read(1024)
            if not new:
                break
            done += len(new)
            if percent != int(done * 100 / length):
                percent = int(done * 100 / length)
                self.stdout.write('{0} ({1:02}%)'.format(self.nb, percent))
            current += new
            while True:
                match = row.search(current)
                if not match:
                    break
                cols = [unescape(s.decode('utf8')) for s in col.split(match.group(1))]
                current = match.group(2)
                self.extract_line(cols)

    def handle(self, *args, **options):
        if not HOST:
            raise CommandError("ENTRECLES_HOST environment variable is not set")
        if not LOGIN:
            raise CommandError("ENTRECLES_LOGIN environment variable is not set")
        if not PASSWORD:
            raise CommandError("ENTRECLES_PASSWORD environment variable are not set")

        self.session = requests.Session()

        self.get('Accueil.aspx')

        params = {
            'ctl00$MainContent$login': LOGIN,
            'ctl00$MainContent$password': PASSWORD,
            'ctl00$MainContent$_btnValider': 'Se connecter',
        }
        self.post('Default.aspx', params, event_validation=True)
        error = self.tree.get_element_by_id('ctl00__erreur__lblErreur', None)
        if error is not None:
            self.stderr.write('Erreur: ' + error.text_content())
            exit(1)

        if FONCTION:
            fonctions = {o.text: o.get('value') for o in self.tree.get_element_by_id('ctl00__ddDelegations')}
            try:
                fonction = fonctions[FONCTION]
            except KeyError:
                self.stderr.write(u'Fonction {0} not in {1}'.format(FONCTION, ', '.join(fonctions)))
                exit(1)
        else:
            fonction = self.tree.get_element_by_id('ctl00__ddDelegations')[0]

        params = {
            '__EVENTTARGET': 'ctl00$_ddDelegations',
            '__EVENTARGUMENT': '',
            '__aspxlab_obj_states': '',
            '__LASTFOCUS': '',
            'ctl00$_tbRechAdherent': '',
            'ctl00$_tbRechStructure': '',
            'ctl00$_ddDelegations': fonction,
            'ctl00$RechercheRapideDociment$_tbTitre': '',
        }
        self.post('Accueil.aspx', params, event_validation=True)

        params = {
            '__EVENTTARGET': 'ctl00$_ddSaisons',
            '__EVENTARGUMENT': '',
            '__aspxlab_obj_states': '',
            '__LASTFOCUS': '',
            'ctl00$_tbRechAdherent': '',
            'ctl00$_tbRechStructure': '',
            'ctl00$_ddDelegations': fonction,
            'ctl00$_ddSaisons': str(SEASON),
            'ctl00$RechercheRapideDociment$_tbTitre': '',
        }
        self.post('Accueil.aspx', params, event_validation=True)

        if options['update_structures']:
            self.get_structure('0000000000', recursive=True)

        self.get('Adherents/ExtraireAdherents.aspx')

        params = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__aspxlab_obj_states': '',
            '__LASTFOCUS': '',
            'ctl00$_tbRechAdherent': '',
            'ctl00$_tbRechStructure': '',
            'ctl00$_ddDelegations': fonction,
            'ctl00$_ddSaisons': SEASON,
            'ctl00$RechercheRapideDociment$_tbTitre': '',
            'ctl00$MainContent$_ddlRequetesExistantes': '-1',
            'ctl00$MainContent$_tbNomNouvelleRequete': '',
            'ctl00$MainContent$_selecteur$_tbCode': STRUCTURE,
            'ctl00$MainContent$_selecteur$_btnValider.x': '28',
            'ctl00$MainContent$_selecteur$_btnValider.y': '12',
            'ctl00$MainContent$_tbCodesTarifs': '',
            'ctl00$MainContent$_ddCategorieMembre': '-1',
            'ctl00$MainContent$_ddTypeInscription': '-1',
            'ctl00$MainContent$ADH': '_rbTous',
            'ctl00$MainContent$_ddSpecialite': '-1',
            'ctl00$MainContent$_ddTypeContact': '-1',
            'ctl00$MainContent$_ddDiplome': '-1',
            'ctl00$MainContent$_ddQualification': '-1',
            'ctl00$MainContent$_ddFormation': '-1',
            'ctl00$MainContent$_ddRevue': '-1',
            'ctl00$MainContent$_ddCategorieSP': '-1',
            'ctl00$MainContent$_ddDecouverteEcle': '-1',
            'ctl00$MainContent$_ddInteret': '-1',
        }
        self.post('Adherents/ExtraireAdherents.aspx', params)

        params = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__aspxlab_obj_states': '',
            '__LASTFOCUS': '',
            'ctl00$_tbRechAdherent': '',
            'ctl00$_tbRechStructure': '',
            'ctl00$_ddDelegations': fonction,
            'ctl00$_ddSaisons': SEASON,
            'ctl00$RechercheRapideDociment$_tbTitre': '',
            'ctl00$MainContent$_ddlRequetesExistantes': '-1',
            'ctl00$MainContent$_tbNomNouvelleRequete': '',
            'ctl00$MainContent$_selecteur$_tbCode': STRUCTURE,
            'ctl00$MainContent$_cbRecursif': 'on',
            'ctl00$MainContent$_tbCodesTarifs': '',
            'ctl00$MainContent$_ddCategorieMembre': '-1',
            'ctl00$MainContent$_ddTypeInscription': '-1',
            'ctl00$MainContent$ADH': '_rbTous',
            'ctl00$MainContent$_ddSpecialite': '-1',
            'ctl00$MainContent$_ddTypeContact': '-1',
            'ctl00$MainContent$_ddDiplome': '-1',
            'ctl00$MainContent$_ddQualification': '-1',
            'ctl00$MainContent$_ddFormation': '-1',
            'ctl00$MainContent$_ddRevue': '-1',
            'ctl00$MainContent$_ddCategorieSP': '-1',
            'ctl00$MainContent$_ddDecouverteEcle': '-1',
            'ctl00$MainContent$_ddInteret': '-1',
            'ctl00$MainContent$_cbExtraireIndividu': 'on',
            # 'ctl00$MainContent$_cbExtraireParents': 'on',
            'ctl00$MainContent$_cbExtraireInscription': 'on',
            'ctl00$MainContent$_cbExtraireAdhesion': 'on',
            'ctl00$MainContent$_btnExporter.x': '32',
            'ctl00$MainContent$_btnExporter.y': '8',
        }
        self.post('Adherents/ExtraireAdherents.aspx', params, stream=True)

        self.extract(self.response.raw, int(self.response.headers['content-length']))

        self.stdout.write('Done')

    def get_children(self):
        other_pages = []
        children = []
        for row in self.tree.get_element_by_id('ctl00_ctl00_MainContent_DivsContent__gvEnfants'):
            if row.get('class') == 'pagination':
                other_pages = [p.text_content() for p in row[0][0][0] if p[0].tag == 'a']
            if row.get('class') not in ('ligne1', 'ligne2'):
                continue
            children.append(row[0][0].text)
        for page in other_pages:
            params = {
                '__EVENTTARGET': 'ctl00$ctl00$MainContent$DivsContent$_gvEnfants',
                '__EVENTARGUMENT': 'Page$' + page,
                '__aspxlab_obj_states': '(::46:(ctl00_ctl00_MainContent_TabsContent_ctl00:1,))',
                '__LASTFOCUS': '',
            }
            self.post(self.response.url, params, event_validation=True)
            for row in self.tree.get_element_by_id('ctl00_ctl00_MainContent_DivsContent__gvEnfants'):
                if row.get('class') not in ('ligne1', 'ligne2'):
                    continue
                children.append(row[0][0].text)
        return children

    def get_structure(self, number, parent=None, recursive=False):
        self.get('Recherche.aspx?type=str&text={0}'.format(number))
        name = self.tree.get_element_by_id('ctl00_ctl00_MainContent_DivsContent__resume__lblNom').text
        type = self.tree.get_element_by_id('ctl00_ctl00_MainContent_DivsContent__resume__lblType').text.rstrip()
        if type in ("Groupe local", "Service vacances"):
            type = "Structure locale d'activité"
        if type in ("Départementale fonctionnel", "Délégation départementale"):
            type = "Département"
        type = dict((val, key) for key, val in Structure.TYPE_CHOICES)[type]
        try:
            sous_type_id = 'ctl00_ctl00_MainContent_DivsContent__resume__lbSouType'
            subtype = self.tree.get_element_by_id(sous_type_id).text.rstrip()
        except KeyError:
            subtype = None
        else:
            subtype = dict((val, key) for key, val in Structure.SUBTYPE_CHOICES)[subtype]
        code_struct_id = 'ctl00_ctl00_MainContent_DivsContent__resume__lblCodeStructure'
        assert number == self.tree.get_element_by_id(code_struct_id).text

        if number == '0000000000':
            parent = None
        elif parent is None:
            parents_id = 'ctl00_ctl00_MainContent_DivsContent__gvParents'
            parent_number = self.tree.get_element_by_id(parents_id)[1][0].text_content()
            try:
                parent = Structure.objects.get(number=parent_number)
            except Structure.DoesNotExist:
                parent = self.get_structure(parent_number)

        if recursive:
            children = self.get_children()

        defaults = {
            'name': name,
            'type': type,
            'subtype': subtype,
            'parent': parent,
        }
        structure, created = Structure.objects.update_or_create(number=number, defaults=defaults)
        values = {
            'number': number,
            'name': name,
            'op': u"created" if created else u"updated",
        }
        self.stdout.write(u"Structure {number} ({name}) {op}".format(**values))
        if recursive:
            for child in children:
                self.get_structure(child, structure, recursive=True)

        return structure
