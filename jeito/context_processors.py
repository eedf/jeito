from django.conf import settings


def conf(request):
    return {
        'conf': {
            'docs_enabled': 'docs' in settings.INSTALLED_APPS,
        },
    }
