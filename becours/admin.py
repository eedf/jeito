from django.contrib import admin
from becours.models import Group, Headcount


class HeadCountInline(admin.TabularInline):
    model = Headcount


class GroupAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'name', 'state', 'type', 'comfort', 'number', 'begin', 'end', 'nights', 'overnights', 'hosting_cost', 'price', 'coop_cost', 'additional_cost', 'cost')
    search_fields = ('name', 'firstname', 'lastname', 'email', 'tel')
    list_filter = ('state', 'type', 'comfort')
    date_hierarchy = 'end'
    inlines = (HeadCountInline, )
    ordering = ('begin', )
    list_display_links = ('name', )

    def price(self, obj):
        return obj.overnights and round(obj.hosting_cost / obj.overnights, 2)


admin.site.register(Group, GroupAdmin)
