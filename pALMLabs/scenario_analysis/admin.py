
from django.contrib import admin
from .models import *

# Register your models here.
class ScenarioDataSetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user__username",
        "name",
        "filename",
        "uploaded_at",
        "status",
        "logs",
        "column_names"
    )

class ScenarioValueAdmin(admin.ModelAdmin):
    list_display = (
        "dataset__name",
        "timestep",
        "variable",
        "value",
    )



admin.site.register(ScenarioDataSet, ScenarioDataSetAdmin)
admin.site.register(ScenarioValue, ScenarioValueAdmin)