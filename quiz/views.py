from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from django.views.generic import TemplateView
from .forms import CustomerUserCreationForm, QuestionForm, AnswerFormSet
from django.contrib.auth.decorators import login_required
from .models import Question


class HomeView(TemplateView):
    """
    Serves the main homepage
    """

    template_name = "quiz/home.html"


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
