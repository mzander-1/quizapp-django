from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Question, Answer, Course


class CustomerUserCreationForm(UserCreationForm):
    """
    A custom form for user registration.
    We can add more fields (e.g. email) later if needed
    """

    # We define this class to potentially customize user creation in the future.
    # For now, it simply inherits from UserCreationForm without changes.
    pass


class QuestionForm(forms.ModelForm):
    """
    Form for creating or updating a Question.
    """

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        help_text="Choose the course for this question.",
    )

    class Meta:
        model = Question
        fields = ["course", "text", "explanation"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full border-gray-300 rounded-md shadow-sm",
                }
            ),
            "explanation": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full border-gray-300 rounded-md shadow-sm",
                }
            ),
            "course": forms.Select(
                attrs={"class": "w-full border-gray-300 rounded-md shadow-sm"}
            ),
        }
        labels = {
            "text": "Fragentext",
            "explanation": "Erklärung (optional)",
            "course": "Kurs (optional)",
        }


class BaseAnswerInlineFormSet(BaseInlineFormSet):
    """
    Custom formset to ensure at least one correct answer is provided.
    """

    def clean(self):
        super().clean()

        if not self.is_valid():
            return

        correct_answer_count = 0
        has_at_least_one_answer = False

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            has_at_least_one_answer = True
            if form.cleaned_data.get("is_correct"):
                correct_answer_count += 1

        if not has_at_least_one_answer:
            raise forms.ValidationError("Please provide at least one answer.")

        if correct_answer_count == 0:
            raise forms.ValidationError("Please mark one answer as correct.")

        if correct_answer_count > 1:
            raise forms.ValidationError("Only one answer can be marked as correct.")


# Create the inline formset for Answers related to a Question
AnswerFormSet = inlineformset_factory(
    Question,  # Object parent model
    Answer,  # Object child model
    fields=("text", "is_correct"),  # Fields to include in the formset
    formset=BaseAnswerInlineFormSet,  # Custom formset class for validation
    extra=4,  # Number of extra forms to display
    max_num=4,  # Maximum number of forms allowed
    can_delete=False,  # Disable deletion of answers (can be changed if needed)
)
