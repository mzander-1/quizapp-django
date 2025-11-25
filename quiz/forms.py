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
                    "class": "w-full border-gray-300 rounded-md shadow-sm max-length-500",
                }
            ),
            "explanation": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full border-gray-300 rounded-md shadow-sm max-length-1000",
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

    def clean_text(self):
        """
        Validates the length of the text field
        """
        text = self.cleaned_data.get("text")
        if text and len(text) > 500:
            raise forms.ValidationError(
                f"Der Fragentext darf maximal 500 Zeichen lang sein."
                f" (Aktuelle Länge: {len(text)})"
            )

        return text

    def clean_explanation(self):
        """
        Validates the length of the explanation field
        """
        explanation = self.cleaned_data.get("explanation")
        if explanation and len(explanation) > 1000:
            raise forms.ValidationError(
                f"Die Erklärung darf maximal 1000 Zeichen lang sein."
                f" (Aktuelle Länge: {len(explanation)})"
            )

        return explanation


class AnswerForm(forms.ModelForm):
    """
    Form for creating or updating an Answer.
    Used within an inline formset.
    """

    class Meta:
        model = Answer
        fields = ["text", "is_correct"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "w-full border-gray-300 rounded-md shadow-sm autosize-textarea",
                    "placeholder": "Antworttext eingeben...",
                }
            ),
            "is_correct": forms.CheckboxInput(
                attrs={
                    "class": "h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                }
            ),
        }
        labels = {"text": "Antworttext", "is_correct": "Richtige Antwort"}

    def clean_text(self):
        """
        Validates the length of the answer text field
        """
        text = self.cleaned_data.get("text")
        if text and len(text) > 500:
            raise forms.ValidationError(
                f"Der Antworttext darf maximal 500 Zeichen lang sein."
                f" (Aktuelle Länge: {len(text)})"
            )

        return text


class BaseAnswerInlineFormSet(BaseInlineFormSet):
    """
    Custom formset to ensure at least one correct answer is provided.
    """

    def clean(self):
        """
        Validates that:
        1. At least one answer is provided
        2. Exactly one answer is marked as correct
        """
        super().clean()

        # Don't validate if there are already errors in individual forms
        if any(self.errors):
            return

        correct_answer_count = 0
        has_at_least_one_answer = False
        filled_forms_count = 0

        for i, form in enumerate(self.forms):

            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            if form.cleaned_data.get("text"):
                filled_forms_count += 1
                has_at_least_one_answer = True

                if form.cleaned_data.get("is_correct"):
                    correct_answer_count += 1

        if not has_at_least_one_answer:
            error_msg = "Bitte geben Sie mindestens eine Antwort ein."
            raise forms.ValidationError(error_msg)

        if correct_answer_count == 0:
            error_msg = "Bitte markieren Sie genau eine Antwort als korrekt."
            raise forms.ValidationError(error_msg)

        if correct_answer_count > 1:
            error_msg = "Es darf nur eine Antwort als korrekt markiert werden."
            raise forms.ValidationError(error_msg)


# Create the inline formset for Answers related to a Question
AnswerFormSet = inlineformset_factory(
    Question,  # Object parent model
    Answer,  # Object child model
    form=AnswerForm,  # Form class to use for each answer
    formset=BaseAnswerInlineFormSet,  # Custom formset class for validation
    extra=4,  # Number of extra forms to display
    max_num=4,  # Maximum number of forms allowed
    can_delete=False,  # Disable deletion of answers (can be changed if needed)
    validate_max=True,  # Ensure max_num is enforced
)


class CreateGameForm(forms.Form):
    """
    Form to create a new game session by selecting a course.
    """

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        label="Wähle einen Kurs",
        empty_label="-- Bitte wählen --",
        widget=forms.Select(
            attrs={"class": "w-full border-gray-300 rounded-md shadow-sm"}
        ),
    )


class JoinGameForm(forms.Form):
    """
    Form to join an existing game session by entering a 6-digit game session code.
    """

    join_code = forms.CharField(
        label="Spielcode eingeben",
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border-gray-300 rounded-md shadow-sm",
                "placeholder": "ABC123",
            }
        ),
    )
