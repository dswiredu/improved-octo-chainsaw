from django.contrib import admin
from .models import *

# Register your models here.
class HistoricalPriceAdmin(admin.ModelAdmin):
    list_display = ('date', 'open_price', 'close_price', 'high_price', 'low_price', 'volume')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_id',)

class AccountAdmin(admin.ModelAdmin):
    list_display = ('client__client_id','account_id')

class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('symbol',)

class PositionSnapshotAdmin(admin.ModelAdmin):
    list_display = ('date', 'account__account_id', 'instrument__symbol', 'market_value')
    


admin.site.register(HistoricalPrice, HistoricalPriceAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(PositionSnapshot, PositionSnapshotAdmin)