# coding: utf8

import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='jeito',
    version='1.0.0.dev0',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='Management tools for Bécours Hamlet.',
    long_description=README,
    url='https://gitlab.com/eedf/jeito',
    author='Gaël Utard',
    author_email='gael.utard@eedf.asso.fr',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'Django>=2.1',
        'django-crispy-forms>=1.7',
        'django-cuser>=2017.3.16',
        'django-debug-toolbar>=1.11',
        'django-filter>=2.1',
        'django-haystack>=2.8',
        'django-mptt>=0.9',
        'django-tagulous>=0.13',
        'django-tracking2>=0.5',
        'djangorestframework>=3.9',
        'elasticsearch>=5.5',
        'factory-boy>=2.11',
        'flake8>=3.7',
        'google-api-python-client>=1.6',
        'gunicorn>=19.9',
        'lxml>=4.3',
        'psycopg2>=2.7',
        'requests-mock>=1.5',
        'tika>=1.13',
    ],
)
