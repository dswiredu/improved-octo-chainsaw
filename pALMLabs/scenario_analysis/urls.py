from django.urls import path

from .views import upload_scenarios, compare_scenarios

urlpatterns = [
    path("upload-scenarios/", upload_scenarios, name="upload-scenarios"),
    path("compare-scenarios/", compare_scenarios, name="compare-scenarios"),
]
