# -*- coding: utf8 -*-

from django.contrib import admin
from .models import Structure, Function, Rate, Person, Adhesion


@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'type', 'parent')
    search_fields = ('number', 'name')
    list_filter = ('type', )


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ('code', 'season', 'name_m', 'name_f')
    search_fields = ('code', 'name_m', 'name_f')
    list_filter = ('season', )


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'rate', 'rate_after_tax_ex', 'bracket', 'category')
    list_filter = ('category', 'bracket')
    search_fields = ('name', )


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('number', 'first_name', 'last_name')
    search_fields = ('number', 'first_name', 'last_name')


@admin.register(Adhesion)
class AdhesionAdmin(admin.ModelAdmin):
    list_display = ('person', 'season', 'date', 'rate', 'structure', 'function')
    search_fields = ('person__number', 'person__first_name', 'person__last_name')
    list_filter = ('season', 'rate')
    date_hierarchy = 'date'
