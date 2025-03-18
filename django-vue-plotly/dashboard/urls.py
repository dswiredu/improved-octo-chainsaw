from django.urls import path
from . import views
from .admin import admin_site

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('ticker/<str:symbol>/', views.ticker_detail, name='ticker_detail'),
    path("search_suggestions/", views.ticker_suggestions, name='ticker_suggestions'),
    path('admin/', admin_site.urls),
]
