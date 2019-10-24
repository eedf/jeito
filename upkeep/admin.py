from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Issue, Place, Priority, Skill


@admin.register(Place)
class PlaceAdmin(MPTTModelAdmin):
    list_display = ('title', )
    search_fields = ('title', )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('title', )
    search_fields = ('title', )


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('title', )
    search_fields = ('title', )


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'place', 'skill')
    list_filter = ('priority', 'place', 'skill')
    search_fields = ('title', 'description')
    raw_id_fields = ('blocks', )
