from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from .forms import (
    CustomerUserCreationForm,
    QuestionForm,
    AnswerFormSet,
    CreateGameForm,
    JoinGameForm,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Question, GameSession, GameParticipant


# HOMEPAGE
@login_required
def home(request):
    """
    Homepage. Shows Forms to create and join game sessions.
    """
    create_form = CreateGameForm()
    join_form = JoinGameForm()

    active_sessions = GameSession.objects.filter(
        participants__user=request.user, status="LOBBY"
    ).distinct()

    return render(
        request,
        "quiz/home.html",
        {
            "create_form": create_form,
            "join_form": join_form,
            "active_sessions": active_sessions,
        },
    )


# USER REGISTRATION
def register_view(request):
    """
    Handles user registration.
    """

    if request.method == "POST":
        form = CustomerUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomerUserCreationForm()

    return render(request, "quiz/register.html", {"form": form})


# QUESTION SUBMISSION AND EDITING
@login_required
def my_question_list(request):
    """
    Displays a list of questions created by the logged-in user.
    """
    questions = Question.objects.filter(creator=request.user).order_by("-created_at")
    return render(request, "quiz/my_questions.html", {"questions": questions})


@login_required
def create_question(request):
    """
    View to create a new question and their answers.
    """

    if request.method == "POST":
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST)

        if question_form.is_valid() and answer_formset.is_valid():
            question = question_form.save(commit=False)
            question.creator = request.user
            question.status = "PENDING"
            question.save()

            answer_formset.instance = question
            answer_formset.save()

            return redirect("my_questions")
        else:
            pass  # Form is invalid, will re-render with errors

    else:
        question_form = QuestionForm()
        answer_formset = AnswerFormSet()

    return render(
        request,
        "quiz/question_form.html",
        {
            "question_form": question_form,
            "answer_formset": answer_formset,
            "page_title": "Neue Frage erstellen",
        },
    )


@login_required
def update_question(request, pk):
    """
    View to update an existing question and its answers.
    """

    question = get_object_or_404(Question, pk=pk, creator=request.user)

    # User should only edit questions that are still pending
    if question.status != "PENDING":
        # TODO: Show a message that only pending questions can be edited
        return redirect("my_questions")

    if request.method == "POST":
        question_form = QuestionForm(request.POST, instance=question)
        answer_formset = AnswerFormSet(request.POST, instance=question)

        if question_form.is_valid() and answer_formset.is_valid():
            question_form.save()
            answer_formset.save()

            return redirect("my_questions")
        else:
            question_form = QuestionForm(instance=question)
            answer_formset = AnswerFormSet(instance=question)

    return render(
        request,
        "quiz/question_form.html",
        {
            "question_form": question_form,
            "answer_formset": answer_formset,
            "page_title": f"Frage '{question.text[:20]}...' bearbeiten",
        },
    )


# GAME LOGIC
QUESTIONS_PER_GAME = 10


@login_required
def create_game_session(request):
    """
    Creates a new game session (Lobby).
    Called via POST from the CreateGameForm on the homepage.
    """

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    form = CreateGameForm(request.POST)
    if form.is_valid():
        course = form.cleaned_data["course"]

        # 1. Check if there are enough questions in the selected course
        questions = Question.objects.filter(
            course=course,
            status="APPROVED",
        )

        if questions.count() < QUESTIONS_PER_GAME:
            messages.error(
                request,
                f"Fehler: Der Kurs '{course.name}' hat nicht genügend freigegebene Fragen (mindestens {QUESTIONS_PER_GAME} benötigt). Bitte wählen Sie einen anderen Kurs oder erstellen Sie mehr Fragen.",
            )
            return redirect("home")

        # 2. Choose random questions for the game session
        selected_questions = questions.order_by("?")[:QUESTIONS_PER_GAME]

        # 3. Create the game session (model generates unique join code)
        game_session = GameSession.objects.create(
            course=course,
            game_mode="COOP",
            status="LOBBY",
        )
        game_session.questions.set(selected_questions)

        # 4. Add the creating user as a participant
        GameParticipant.objects.create(session=game_session, user=request.user)

        # 5. Redirect to the game lobby
        messages.success(
            request,
            f"Spiel-Lobby für Kurs '{course.name}' wurde erstellt.",
        )
        return redirect("game_lobby", join_code=game_session.join_code)

    else:
        messages.error(
            request,
            "Fehler beim Erstellen der Spiel-Lobby. Bitte versuchen Sie es erneut.",
        )
        return redirect("home")


@login_required
def join_game_session(request):
    """
    Joins an existing game session (Lobby) using a join code.
    Called via POST from the JoinGameForm on the homepage.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    form = JoinGameForm(request.POST)
    if form.is_valid():
        join_code = form.cleaned_data["join_code"].upper()

        try:
            # 1. Find the game session by join code
            game_session = GameSession.objects.get(join_code=join_code, status="LOBBY")
        except GameSession.DoesNotExist:
            messages.error(
                request,
                f"Fehler: Keine aktive Spiel-Lobby mit dem Code '{join_code}' gefunden oder das Spiel ist bereits gestartet.",
            )
            return redirect("home")

        # 2. Add the user as a participant if not already joined
        # get_or_create prevents duplicate entries
        GameParticipant.objects.get_or_create(session=game_session, user=request.user)

        # 3. Redirect to the game lobby
        messages.success(
            request,
            f"Erfolgreich der Spiel-Lobby '{join_code}' beigetreten.",
        )
        return redirect("game_lobby", join_code=game_session.join_code)

    else:
        messages.error(
            request,
            "Fehler beim Beitreten der Spiel-Lobby. Bitte überprüfen Sie den Code und versuchen Sie es erneut.",
        )
        return redirect("home")


@login_required
def game_lobby(request, join_code):
    """
    Displays the game lobby where players wait before starting the game.
    """
    game_session = get_object_or_404(
        GameSession, join_code=join_code.upper(), status="LOBBY"
    )

    # Ensure the user is a participant of this game session
    if not GameParticipant.objects.filter(user=request.user).exists():
        messages.error(
            request,
            "Sie sind kein Teilnehmer dieser Spiel-Lobby.",
        )
        return redirect("home")

    host_participant = game_session.participants.first()
    is_host = host_participant.user == request.user

    return render(
        request,
        "quiz/game_lobby.html",
        {
            "game_session": game_session,
            "is_host": is_host,
        },
    )


@login_required
def poll_lobby_participants(request, join_code):
    """
    Endpoint to poll the current list of participants in the game lobby.
    Returns a partial HTML list for HTMX.
    """
    game_session = get_object_or_404(
        GameSession,
        join_code=join_code.upper(),
    )

    return render(
        request,
        "quiz/partials/_lobby_participant_list.html",
        {
            "game_session": game_session,
        },
    )
