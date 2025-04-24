from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('overview/', views.index, name='overview'),
    path('analytics/', views.index, name='analytics'),
    path('admin_settings/', views.index, name='admin_settings'),
    path('load_data/', views.index, name='load_data'),
]
