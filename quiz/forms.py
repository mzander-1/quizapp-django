from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomerUserCreationForm(UserCreationForm):
    """
    A custom form for user registration.
    We can add more fields (e.g. email) later if needed
    """

    # We define this class to potentially customize user creation in the future.
    # For now, it simply inherits from UserCreationForm without changes.
    pass
