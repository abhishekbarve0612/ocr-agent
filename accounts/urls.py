from django.urls import path, include
from django.contrib.auth import views as auth_views

from accounts.forms import LoginForm

app_name = 'accounts'

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html", form_class=LoginForm), name="login"),
    path("", include("django.contrib.auth.urls")),
]
