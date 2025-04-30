from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('overview/', views.index, name='overview'),
    path('analytics/', views.date_test, name='analytics'),
    path('admin_settings/', views.index, name='admin_settings'),
    path('load_data/', views.index, name='load_data'),
    path('update_chart', views.update_line_chart, name="update_chart"),
    path('export_data', views.export_data, name="export_data"),
    path('render_table', views.render_table, name="render_table"),
    path('nav_test', views.nav_test, name="nav_test"),
]
