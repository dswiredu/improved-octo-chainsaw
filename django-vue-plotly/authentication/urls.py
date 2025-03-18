from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path("login/", LoginView.as_view(template_name="authentication/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),  # No next_page="login" needed; Django handles it by design!
]