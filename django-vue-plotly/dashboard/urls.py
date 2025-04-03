from django.urls import path
from . import views
from .admin import admin_site

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('ticker/<str:symbol>/', views.ticker_detail, name='ticker_detail'),
    path("search_suggestions/", views.ticker_suggestions, name='ticker_suggestions'),
    path("compare/", views.compare_tickers, name="compare_tickers"),
    path("compart_line_chart/", views.compare_line_chart, name="compare_line_chart"),
    path("compare_risk_return/", views.compare_risk_return, name="compare_risk_return"),
    path('admin/', admin_site.urls),
]
