from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
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
    path("game/create/", views.create_game_session, name="create_game"),
    path("game/join/", views.join_game_session, name="join_game"),
    path("game/<str:join_code>/lobby/", views.game_lobby, name="game_lobby"),
    path(
        "game/<str:join_code>/poll_lobby/",
        views.poll_lobby_participants,
        name="poll_lobby",
    ),
    path(
        "game/<str:join_code>/poll_start/",
        views.poll_game_start,
        name="poll_game_start",
    ),
    path("game/<str:join_code>/start/", views.start_game, name="start_game"),
    path("game/<str:join_code>/play/", views.game_view, name="game_view"),
    path(
        "game/<str:join_code>/state/", views.game_state_poller, name="game_state_poller"
    ),
    path(
        "game/<str:join_code>/submit/<int:answer_pk>/",
        views.submit_answer,
        name="submit_answer",
    ),
    path("game/<str:join_code>/next/", views.next_question, name="next_question"),
    path("game/<str:join_code>/results/", views.game_results, name="game_results"),
]
