from django.contrib import admin
from .models import ReportRun

from dashboard.admin import admin_site

# Register your models here.
class ReportRunAdmin(admin.ModelAdmin):
    list_display = ("ticker", "report_type", "status", "run_at")
    list_filter = ("report_type", "status")
    search_fields = ("ticker",)
    ordering = ("-run_at",)


admin_site.register(ReportRun, ReportRunAdmin)
