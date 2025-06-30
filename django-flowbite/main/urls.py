from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="s-curve-load"),
    path("run-model", views.index, name="run-model"),
    path("upload-scenarios", views.index, name="upload-scenarios"),
    path("compare-scenarios", views.index, name="compare-scenarios"),
    path("reports", views.index, name="reports"),
    path("load", views.index, name="load"),
    path("clean", views.index, name="clean"),
    path("manage-users", views.index, name="manage-users"),
    path("view-logs", views.index, name="view-logs"),
    path("docs", views.index, name="docs"),
    path("preferences", views.index, name="preferences"),
    path("api-keys", views.index, name="api-keys"),
]
