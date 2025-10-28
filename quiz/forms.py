from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomerUserCreationForm(UserCreationForm):
    """
    A custom form for user registration.
    We can add more fields (e.g. email) later if needed
    """

    class Meta:
        model = User
        fields = ("username",)
