from django.contrib import admin
from .models import HistoricalPrice

# Register your models here.
class HistoricalPriceAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'exchange')


admin.register(HistoricalPrice, HistoricalPriceAdmin)