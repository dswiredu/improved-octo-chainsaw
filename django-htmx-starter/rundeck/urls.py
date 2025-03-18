from django.urls import path
from . import views

urlpatterns = [
    path("", views.rundeck_view, name="rundeck"),  # Load script execution UI
    path("execute-script/", views.execute_script, name="execute_script"),  # Run scripts
    path("execution-logs/", views.execution_logs, name="execution_logs"),  # View logs list
    path("execution-logs/<int:execution_id>/", views.get_execution_logs, name="get_execution_logs"),  # Fetch specific logs
]
