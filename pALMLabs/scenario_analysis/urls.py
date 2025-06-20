from django.urls import path
from . import views

app_name = "scenario_analysis"

urlpatterns = [
    path("upload-scenarios/", views.upload_scenarios, name="upload-scenarios"),
    path(
        "dataset-status-table/", views.dataset_status_table, name="dataset-status-table"
    ),
    path(
        "start-background-processing/",
        views.start_background_processing,
        name="start-background-processing",
    ),
    path("clear-datasets/", views.clear_datasets, name="clear-datasets"),
    path("compare-scenarios/", views.compare_scenarios, name="compare-scenarios"),
    path("search-scenarios/", views.search_scenarios, name="search-scenarios"),
    path("search-columns/", views.search_columns, name="search-columns"),
    path(
        "add-scenario-to-pill/", views.add_scenario_to_pill, name="add_scenario_to_pill"
    ),
    path("add-column-to-pill/", views.add_column_to_pill, name="add_column_to_pill"),
]
