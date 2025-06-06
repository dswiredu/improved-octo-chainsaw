from django.urls import path

from .views import s_curve_calibration

urlpatterns = [
    path("", s_curve_calibration.load_data, name="s-curve-load"),
    path("results/", s_curve_calibration.get_results, name="s-curve-results"),
    path("export/", s_curve_calibration.export_data_to_csv, name="export_data_to_csv"),
    path("toggle_graph_table/", s_curve_calibration.toggle_graph_table, name="toggle_graph_table"),
    path("scale_cashflows/", s_curve_calibration.get_scaled_results, name="scale_cashflow_results"),
]
