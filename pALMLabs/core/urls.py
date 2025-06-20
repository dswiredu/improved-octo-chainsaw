from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("after-login/", views.post_login_redirect, name="post-login-redirect"),
]
