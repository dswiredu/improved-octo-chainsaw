from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('update_index_contents/', views.update_index_contents, name="update_index_contents"),
]
