# -*- coding: utf8 -*-

from django.contrib import admin
from .models import Structure, Function, Rate, Person, Adhesion, Nomination


@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'type', 'subtype', 'parent')
    search_fields = ('number', 'name')
    list_filter = ('type', 'subtype')


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ('code', 'season', 'name_m', 'category')
    search_fields = ('code', 'name_m', 'name_f')
    list_filter = ('season', 'category')

    def get_actions(self, request):
        def make_func(index):
            def func(modeladmin, request, queryset):
                queryset.update(category=index)

            return func

        actions = super(FunctionAdmin, self).get_actions(request)
        for index, name in Function.CATEGORY_CHOICES:
            key = "set_category_{}".format(index)
            short_description = "Placer dans {}".format(name)
            actions[key] = (make_func(index), key, short_description)
        return actions


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'rate', 'rate_after_tax_ex', 'bracket', 'category')
    list_filter = ('season', 'category', 'bracket')
    search_fields = ('name', )


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('number', 'first_name', 'last_name')
    search_fields = ('number', 'first_name', 'last_name')


class NominationInline(admin.TabularInline):
    model = Nomination


@admin.register(Adhesion)
class AdhesionAdmin(admin.ModelAdmin):
    list_display = ('person', 'season', 'date', 'rate', 'structure')
    search_fields = ('person__number', 'person__first_name', 'person__last_name')
    list_filter = ('season', 'rate')
    inlines = (NominationInline, )
    raw_id_fields = ('person', )
    date_hierarchy = 'date'
