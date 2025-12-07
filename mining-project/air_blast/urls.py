from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import index, export_excel, load_model_form

urlpatterns = [
    path("", login_required(index), name="air-blast-index"),
    path("export-excel/", login_required(export_excel), name="air_blast_export_excel"),
    path("load-model-form/", load_model_form, name="air_blast_load_model_form"),
]
