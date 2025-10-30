from django.contrib import admin
from quiz.models import (
    Course,
    Question,
    Answer,
    GameSession,
    GameParticipant,
    TeamGameAnswer,
)


class AnswerInline(admin.TabularInline):
    """
    Inline admin interface for Answers within a Question.
    """

    model = Answer
    extra = 4  # Number of extra answer fields to display
    fields = ("text", "is_correct")


class GameParticipantInline(admin.TabularInline):
    """
    Inline admin interface for GameParticipants within a GameSession.
    """

    model = GameParticipant
    extra = 0  # Number of extra participant fields to display
    readonly_fields = (
        "user",
        "score",
    )
    can_delete = False


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Admin interface for Course model.
    """

    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Question model.
    """

    model = Question
    inlines = [AnswerInline]

    list_display = ("text", "course", "status", "creator", "created_at")
    list_filter = ("status", "course", "creator")
    search_fields = (
        "text",
        "explanation",
        "course__name",
    )

    actions = ["approve_questions"]

    def approve_questions(self, request, queryset):
        """
        Custom admin action to approve selected questions.
        """
        queryset.update(status="APPROVED")
        self.message_user(
            request,
            f"{queryset.count()} question(s) successfully approved.",
        )

    approve_questions.short_description = "Mark selected questions as approved"


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for active GameSession.
    """

    list_display = (
        "join_code",
        "course",
        "status",
        "game_mode",
        "created_at",
    )
    list_filter = ("status", "course", "game_mode")
    readonly_fields = ("join_code", "created_at", "current_question")
    inlines = [GameParticipantInline]


@admin.register(GameParticipant)
class GameParticipantAdmin(admin.ModelAdmin):
    """
    Admin interface for GameParticipant model.
    """

    list_display = ("user", "session", "score")
    list_filter = ("session",)
    search_fields = ("user__username", "session__join_code")


@admin.register(TeamGameAnswer)
class TeamGameAnswerAdmin(admin.ModelAdmin):
    """
    Admin interface for TeamGameAnswer model.
    READ-ONLY, as it's a log of game activity.
    """

    list_display = (
        "session",
        "question",
        "selected_answer",
        "is_correct",
        "answered_by",
    )
    list_filter = ("session", "is_correct")
    search_fields = ("session__join_code", "question__text")

    def has_add_permission(self, request):
        return False  # Prevent adding new entries via admin

    def has_change_permission(self, request, obj=None):
        return False  # Prevent changing existing entries via admin
