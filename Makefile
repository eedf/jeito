VENV=env

run: $(VENV)/bin/django-admin
	./manage.py runserver 0.0.0.0:8000

$(VENV)/bin/django-admin: $(VENV)/bin/python /usr/bin/virtualenv /usr/include/postgresql/libpq /usr/include/python3.4/pyconfig.h /usr/include/libxml2/libxml/xmlversion.h /usr/bin/xslt-config
	$(VENV)/bin/pip install -r requirements.txt

$(VENV)/bin/python: /usr/bin/virtualenv
	virtualenv -p python3 $(VENV)
	$(VENV)/bin/pip install -U pip

/usr/bin/virtualenv:
	sudo apt-get install -y python-virtualenv

/usr/include/postgresql/libpq:
	sudo apt-get install -y libpq-dev

/usr/include/python3.4/pyconfig.h:
	sudo apt-get install -y libpython3.4-dev

/usr/include/libxml2/libxml/xmlversion.h:
	sudo apt-get install -y libxml2-dev

/usr/bin/xslt-config:
	sudo apt-get install -y libxslt1-dev

/usr/lib/postgresql/9.3/bin/postgres:
	sudo apt-get install -y postgresql-9.3

installdb: /usr/lib/postgresql/9.3/bin/postgres
