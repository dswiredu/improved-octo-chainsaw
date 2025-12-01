from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import index, export_excel, load_model_form

urlpatterns = [
    path("", login_required(index), name="ground-vibration-index"),
    path("export-excel/", login_required(export_excel), name="ground-vibration-export-excel"),
    path("load-model-form/", load_model_form, name="load_model_form"),
]
