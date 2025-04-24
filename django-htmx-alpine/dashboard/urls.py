from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('update_chart', views.update_line_chart, name="update_chart"),
]
