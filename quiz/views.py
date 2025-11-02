from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from django.urls import reverse
from .forms import (
    CustomerUserCreationForm,
    QuestionForm,
    AnswerFormSet,
    CreateGameForm,
    JoinGameForm,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import (
    Course,
    Question,
    GameSession,
    GameParticipant,
    TeamGameAnswer,
    Answer,
)
from django.db.models import F


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
    Displays a list of questions created by the logged-in user,
    with filtering, sorting, and grouping by status.
    """

    # 1. Filter- und Sortierparameter aus der URL (GET-Request) holen
    status_filter = request.GET.get("status")
    course_filter = request.GET.get("course")
    sort_by = request.GET.get("sort_by", "-created_at")  # Standard: Neueste zuerst

    # 2. Basis-Queryset: Nur Fragen des angemeldeten Benutzers
    queryset = Question.objects.filter(creator=request.user)

    # 3. Filter anwenden
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if course_filter:
        queryset = queryset.filter(course_id=course_filter)  # course_id ist effizienter

    # 4. Sortierung anwenden (Whitelist, um Sicherheit zu gewährleisten)
    valid_sorts = ["created_at", "-created_at", "text", "-text"]
    if sort_by in valid_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by("-created_at")  # Fallback auf Standard

    # 5. Fragen nach Status gruppieren
    # Wir bereiten die Gruppen vor, die angezeigt werden sollen
    grouped_questions = {}
    total_questions_found = 0

    # Bestimmen, welche Status-Gruppen wir anzeigen müssen
    # Entweder nur der gefilterte Status, oder alle
    if status_filter:
        statuses_to_show = [s for s in Question.STATUS_CHOICES if s[0] == status_filter]
    else:
        statuses_to_show = Question.STATUS_CHOICES

    # Das bereits gefilterte/sortierte Queryset durchlaufen und Gruppen erstellen
    for code, name in statuses_to_show:
        # Filtern des *bereits gefilterten* Querysets nach dem jeweiligen Status
        questions_in_group = queryset.filter(status=code)

        if questions_in_group.exists():
            grouped_questions[code] = {"name": name, "questions": questions_in_group}
            total_questions_found += questions_in_group.count()

    # 6. Kontext für das Template vorbereiten
    context = {
        "grouped_questions": grouped_questions,
        "all_courses": Course.objects.all(),  # Für den Kurs-Filter-Dropdown
        "status_choices": Question.STATUS_CHOICES,  # Für den Status-Filter-Dropdown
        "current_filters": {
            "status": status_filter,
            "course": course_filter,
            "sort_by": sort_by,
        },
        "total_questions_found": total_questions_found,
    }

    return render(request, "quiz/my_questions.html", context)


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


# GAME SESSION LOGIC
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
        "quiz/partials/_lobby_participants_list.html",
        {
            "game_session": game_session,
        },
    )


# GAMEPLAY LOGIC
@login_required
def poll_game_start(request, join_code):
    """
    Endpoint to poll whether the game has started.
    """

    game_session = get_object_or_404(GameSession, join_code=join_code.upper())

    if game_session.status == "ACTIVE":
        response = HttpResponse()
        response["HX-Redirect"] = reverse("game_view", args=[join_code])
        return response

    return HttpResponse()


@login_required
def start_game(request, join_code):
    """
    Starts the game session. Only the host can start the game.
    """

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    game_session = get_object_or_404(
        GameSession, join_code=join_code.upper(), status="LOBBY"
    )

    host_participant = game_session.participants.order_by("id").first()
    if not host_participant or host_participant.user != request.user:
        messages.error(request, "Nur der Gastgeber kann das Spiel starten.")
        return redirect("game_lobby", join_code=join_code)

    first_question = game_session.questions.order_by("id").first()

    if not first_question:
        messages.error(
            request, "Fehler: Keine Fragen für diese Spiel-Sitzung gefunden."
        )
        return redirect("home")

    game_session.status = "ACTIVE"
    game_session.current_question = first_question
    game_session.save()

    return redirect("game_view", join_code=join_code)


@login_required
def game_view(request, join_code):
    """
    Main game view where questions are presented and answered.
    Renders Template which includes HTMX calls for dynamic updates.
    """

    game_session = get_object_or_404(
        GameSession, join_code=join_code.upper(), participants__user=request.user
    )

    if game_session.status == "FINISHED":
        return redirect("game_results", join_code=join_code)

    if game_session.status == "LOBBY":
        return redirect("game_lobby", join_code=join_code)

    return render(request, "quiz/game_view.html", {"game_session": game_session})


@login_required
def game_state_poller(request, join_code):
    """
    Endpoint to poll the current game state and question.
    Returns partial HTML for HTMX updates.
    """

    game_session = get_object_or_404(
        GameSession, join_code=join_code.upper(), participants__user=request.user
    )

    # 1. If game is finished, redirect to results
    if game_session.status == "FINISHED":
        response = HttpResponse()
        response["HX-Redirect"] = reverse("game_results", args=[join_code])
        return response

    # 2. Check if current question is already answered by participants
    current_question = game_session.current_question

    try:
        team_answer = TeamGameAnswer.objects.get(
            session=game_session,
            question=current_question,
        )
        return render(
            request,
            "quiz/partials/_question_result.html",
            {
                "game_session": game_session,
                "question": current_question,
                "team_answer": team_answer,
                "answered_by_user": (
                    team_answer.answered_by.username
                    if team_answer.answered_by
                    else "jemand"
                ),
            },
        )
    except TeamGameAnswer.DoesNotExist:
        # 3. Question not yet answered, show question

        all_questions = list(
            game_session.questions.order_by("id").values_list("id", flat=True)
        )
        try:
            current_index = all_questions.index(current_question.id)
            question_number = current_index + 1
            total_questions = len(all_questions)
        except (ValueError, AttributeError):
            question_number = "?"
            total_questions = "?"

        return render(
            request,
            "quiz/partials/_game_question.html",
            {
                "game_session": game_session,
                "question": current_question,
                "question_number": question_number,
                "total_questions": total_questions,
            },
        )


@login_required
@require_POST
def submit_answer(request, join_code, answer_pk):
    """
    Endpoint to submit an answer for the current question.
    """

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    game_session = get_object_or_404(
        GameSession, join_code=join_code.upper(), status="ACTIVE"
    )
    current_question = game_session.current_question
    selected_answer = get_object_or_404(Answer, pk=answer_pk, question=current_question)

    team_answer, created = TeamGameAnswer.objects.get_or_create(
        session=game_session,
        question=current_question,
        defaults={
            "selected_answer": selected_answer,
            "answered_by": request.user,
            "is_correct": selected_answer.is_correct,
        },
    )

    if created and team_answer.is_correct:
        GameParticipant.objects.filter(session=game_session).update(
            score=F("score") + 10
        )

    # Render the question result to the user that submitted the answer, after 3 seconds HTMX will poll for the others
    return render(
        request,
        "quiz/partials/_question_result.html",
        {
            "game_session": game_session,
            "question": current_question,
            "team_answer": team_answer,
            "answered_by_user": (
                team_answer.answered_by.username
                if team_answer.answered_by
                else "jemand"
            ),
        },
    )


@login_required
@require_POST
def next_question(request, join_code):
    """
    Endpoint to move to the next question in the game session.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    game_session = get_object_or_404(
        GameSession, join_code=join_code.upper(), status="ACTIVE"
    )
    current_question = game_session.current_question

    all_questions = list(game_session.questions.order_by("id"))

    try:
        current_index = all_questions.index(current_question)
        next_question = all_questions[current_index + 1]

        game_session.current_question = next_question
        game_session.save()

    except (ValueError, IndexError):
        game_session.status = "FINISHED"
        game_session.current_question = None
        game_session.save()

        response = HttpResponse()
        response["HX-Redirect"] = reverse("game_results", args=[join_code])
        return response

    return HttpResponse(
        '<div class="text-center p-10"><h2 class="text-2x1 font-semibold text-gray-700">Lade nächste Frage...</h2></div>   '
    )


@login_required
def game_results(request, join_code):
    """
    Displays the results of the finished game session.
    """

    game_session = get_object_or_404(
        GameSession,
        join_code=join_code,
        status="FINISHED",
        participants__user=request.user,
    )

    return render(request, "quiz/game_results.html", {"game_session": game_session})
