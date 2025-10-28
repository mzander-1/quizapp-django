from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic import TemplateView
from .forms import CustomerUserCreationForm


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
