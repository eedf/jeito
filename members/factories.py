from datetime import date
import factory
from . import models


class StructureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Structure

    number = factory.Sequence(lambda n: "%10d" % n)
    name = factory.Sequence(lambda n: "Name %03d" % n)


class FunctionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Function

    code = factory.Sequence(lambda n: "CD%3d" % n)
    season = 2015
    name_m = factory.Sequence(lambda n: "Function M %03d" % n)
    name_f = factory.Sequence(lambda n: "Function F %03d" % n)


class RateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Rate

    name = factory.Sequence(lambda n: "Rate %3d" % n)
    season = 2015


class MinimalPersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Person

    number = factory.Sequence(lambda n: "%06d" % n)


class PersonFactory(MinimalPersonFactory):
    first_name = factory.Sequence(lambda n: "Firstname %03d" % n)
    last_name = factory.Sequence(lambda n: "Lastname %03d" % n)
    email = factory.Sequence(lambda n: "person%03d@toto.com" % n)
    gender = factory.Sequence(lambda n: n % 2 + 1)


class AdhesionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Adhesion

    person = factory.SubFactory(PersonFactory)
    season = 2016
    date = date(2015, 10, 15)
    rate = factory.SubFactory(RateFactory)
    structure = factory.SubFactory(StructureFactory)
    function = factory.SubFactory(FunctionFactory)
