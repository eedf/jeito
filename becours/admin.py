from django.contrib import admin
from becours.models import Group, Headcount


class HeadCountInline(admin.TabularInline):
    model = Headcount


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'type', 'comfort', 'number', 'begin', 'end', 'nights', 'overnights')
    search_fields = ('name', 'firstname', 'lastname', 'email', 'tel')
    list_filter = ('state', 'type', 'comfort')
    date_hierarchy = 'end'
    inlines = (HeadCountInline, )


admin.site.register(Group, GroupAdmin)
