import datetime
from .settings import *  # NOQA

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'NAME': 'jeito',
        'USER': 'jeito',
        'PASSWORD': '',
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'TIMEOUT': 60 * 10,
        'INDEX_NAME': 'test_index',
    },
}

SECRET_KEY = 'usemeonlyfortest'


def NOW():
    return datetime.datetime(2015, 3, 12, 15, 42, 3)
