from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import index, export_excel, load_model_form

urlpatterns = [
    path("", login_required(index), name="ground-vibration-index"),
    path("export-excel/", login_required(export_excel), name="ground_vibration_export_excel"),
    path("load-model-form/", load_model_form, name="ground_vibration_load_model_form"),
]
