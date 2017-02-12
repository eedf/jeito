from django.contrib import admin
from .models import Report, TeamMember


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    raw_id_fields = ('person', )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('structure', 'season', 'date', 'representative')
    raw_id_fields = ('structure', 'delegate', 'alternate', 'leader', 'treasurer')
    list_filter = ('season', )
    date_hierarchy = 'date'
    inlines = (TeamMemberInline, )
