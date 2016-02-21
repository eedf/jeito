# Jéito

Un espace de documentation participatif

[![Build Status](https://travis-ci.org/eedf/jeito.svg?branch=master)](https://travis-ci.org/eedf/jeito)
[![Coverage Status](https://coveralls.io/repos/github/eedf/jeito/badge.svg?branch=master)](https://coveralls.io/github/eedf/jeito?branch=master)


# Dévelopment

## Installation

Sur une distribution GNU/Linux Ubuntu, dans un shell, exécute les commandes suivantes :

```bash
$ sudo apt-get install git docker.io python3 python-virtualenv python3-dev libpq-dev libxml2-dev libxslt1-dev
$ sudo docker run --name jeito-postgres -e POSTGRES_USER=jeito -p 5432:5432 -d postgres
$ sudo docker run --name jeito-elasticsearch -p 9200:9200 -d elasticsearch
$ sudo docker run --name jeito-tika -p 9998:9998 -d logicalspark/docker-tikaserver
$ git clone https://github.com/eedf/jeito.git
$ cd jeito
$ virtualenv -p python3 env
$ env/bin/pip install -U pip wheel
$ env/bin/pip install -r requirements.txt
$ cp jeito/settings_local.py.template jeito/settings_local.py
$ ./manage.py migrate
```

## Mise à jour

Dans un shell, exécute les commandes suivantes :

```bash
$ cd jeito
$ git pull
$ env/bin/pip install -r requirements.txt
$ ./manage.py migrate
```

## Démarrage

Dans un shell, exécute les commandes suivantes :

```bash
$ sudo docker start jeito-postgres jeito-elasticsearch jeito-tika
$ ./manage.py runserver
```

Puis ouvre un navigateur à l'adresse http://localhost:8000
