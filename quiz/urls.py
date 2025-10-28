from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home page
    path("", views.HomeView.as_view(), name="home"),
    # User registration
    path("register/", views.register_view, name="register"),
    # User login
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="quiz/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    # User logout
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
]
