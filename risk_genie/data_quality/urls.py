from django.urls import path
from . import views


app_name = "data_quality"

urlpatterns = [
    path("", views.overview, name="overview"),
]
