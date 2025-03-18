from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Ticker, TickerMetadata, HistoricalPrice


class TickerAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'exchange')
    search_fields = ('symbol', 'name')
    list_filter = ('sector', 'industry')


class TickerMetadataAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'last_updated', 'market_cap', 'beta')
    search_fields = ('ticker__symbol',)


class HistoricalPriceAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'date', 'close_price', 'volume')
    list_filter = ('ticker', 'date')
    search_fields = ('ticker__symbol',)


class CustomAdminSite(admin.AdminSite):
    """
    Class to add custom django admin links to django admin
    """
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)

        app_list.insert(0, { # Can add more with index 1,2,3...
            'name' : 'Main Dashboard',
            'app_label' : 'dashboard',
            'models' : [
                {'name': '← Back to Dashboard', 'admin_url': reverse('dashboard')}
            ]
        })
        return app_list

admin_site = CustomAdminSite(name="custom_admin")
admin_site.register(Ticker, TickerAdmin)
admin_site.register(TickerMetadata, TickerMetadataAdmin)
admin_site.register(HistoricalPrice, HistoricalPriceAdmin)