from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Course(models.Model):
    """
    Represents a course or module (e.g., "ISEF01").
    Questions can be associtated with a module.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the course/module, e.g., 'ISEF01'",
    )

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    The central class for a single quiz question.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),  # Submitted but not yet reviewed
        ("APPROVED", "Approved"),  # Reviewed and approved
        ("REJECTED", "Rejected"),  # Rejected after review
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,  # If a course is deleted, keep the question but set course to NULL
        null=True,
        blank=True,
        related_name="questions",
        help_text="Optional: The course/module this question belongs to.",
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # If a user is deleted, keep the question but set creator to NULL
        null=True,
        related_name="created_questions",
        help_text="The user who created this question.",
    )
    text = models.TextField(help_text="The text of the question.")
    explanation = models.TextField(
        blank=True,
        null=True,
        help_text="Optional explanation or background information for the question.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        help_text="The review status of the question.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[
            :50
        ]  # Shows first 50 characters of the question text in the admin panel


class Answer(models.Model):
    """
    An answer option belonging to a specific question.
    Each question can have multiple answer options. One of them is marked as correct.
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,  # If a question is deleted, delete its answers as well
        related_name="answers",
        help_text="The question this answer belongs to.",
    )
    text = models.CharField(max_length=500, help_text="The text of the answer option.")
    is_correct = models.BooleanField(
        default=False, help_text="Indicates if this answer is correct."
    )

    def __str__(self):
        return f"({'Correct' if self.is_correct else 'Incorrect'}) {self.text}"


def generate_join_code():
    """
    Generates a unique 6-digit lobby code for game sessions.
    """
    return uuid.uuid4().hex[:6].upper()


class GameSession(models.Model):
    """
    A game session, representing a lobby or an active game.
    Students can join this session to play cooperatively.
    """

    MODE_CHOICES = [
        ("COOP", "Cooperative"),
        # Later we can add competitive modes here
    ]
    STATUS_CHOICES = [
        ("LOBBY", "Lobby (Waiting for players)"),
        ("ACTIVE", "Active (Game in progress)"),
        ("FINISHED", "Ended (Show results)"),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The module from which questions will be drawn for this game session.",
    )
    game_mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default="COOP",
        help_text="The game mode for this session.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="LOBBY",
        help_text="The current status of the game session.",
    )
    join_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_join_code,
        help_text="Unique code for players to join this game session.",
    )
    questions = models.ManyToManyField(Question, related_name="game_sessions")
    current_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # Prevents reverse relation
        help_text="The current question being answered in the game session.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Game {self.join_code} ({self.get_status_display()})"


class GameParticipant(models.Model):
    """
    Links a User to a GameSession.
    Stores the individual player's score.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="game_participations"
    )
    session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE, related_name="participants"
    )
    score = models.IntegerField(default=0, help_text="The player's score in this game.")

    class Meta:
        # A user can't join the same game session multiple times
        unique_together = ("user", "session")

    def __str__(self):
        return f"{self.user.username} in Game {self.session.join_code}"


class TeamGameAnswer(models.Model):
    """
    Stores the (first) answer submitted by a team for a question in a game session.
    In coop mode, the first answer submitted by any team member counts.
    """

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="team_answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="team_answers",
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
    )
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    is_correct = models.BooleanField(
        default=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure one answer per question per game session
        unique_together = ("session", "question")

    def __str__(self):
        return f"Answer for Question {self.question.id} in Game {self.session.id}"
