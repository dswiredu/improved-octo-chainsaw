from django.contrib import admin
from .models import HistoricalPrice

# Register your models here.
class HistoricalPriceAdmin(admin.ModelAdmin):
    list_display = ('date', 'open_price', 'close_price', 'high_price', 'low_price', 'volume')


admin.site.register(HistoricalPrice, HistoricalPriceAdmin)