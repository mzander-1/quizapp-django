from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("register/", views.register_view, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="quiz/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("my-questions/", views.my_question_list, name="my_questions"),
    path("question/new/", views.create_question, name="create_question"),
    path("question/<int:pk>/edit/", views.update_question, name="update_question"),
]
