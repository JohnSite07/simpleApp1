from django.contrib import admin
from .models import Quiz, UploadedFile, Question, QuizSession, UserAnswer

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'quiz_type', 'num_questions', 'created_at']
    list_filter = ['quiz_type', 'created_at']
    search_fields = ['title', 'user__username']
    date_hierarchy = 'created_at'

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'quiz', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'quiz__title']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'question_text', 'correct_answer']
    list_filter = ['quiz__quiz_type', 'created_at']
    search_fields = ['question_text', 'quiz__title']
    ordering = ['quiz', 'order']

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'user', 'score', 'total_questions', 'correct_answers', 'completed_at']
    list_filter = ['completed_at', 'quiz__quiz_type']
    search_fields = ['quiz__title', 'user__username']
    date_hierarchy = 'started_at'

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'user_answer', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['session__user__username', 'question__question_text']
