from django.urls import path
from .views import client_portfolios, overview

urlpatterns = [
    path('', overview.index, name='dashboard'),
    path('overview/', overview.index, name='overview'),
    path('client_portfolios/', client_portfolios.index, name='client_portfolios'),
    path('analytics/', overview.date_test, name='analytics'),
    path('admin_settings/', overview.index, name='admin_settings'),
    path('load_data/', overview.index, name='load_data'),
    path('update_chart', overview.update_line_chart, name="update_chart"),
    path('export_data', overview.export_data, name="export_data"),
    path('render_table', overview.render_table, name="render_table"),
    path('nav_test', overview.nav_test, name="nav_test"),
]
