from django.db import models
from django.contrib.auth.models import User
import json

class Quiz(models.Model):
    """Model to store quiz information"""
    QUIZ_TYPES = [
        ('flashcards', 'Flash Cards'),
        ('multiple_choice', 'Multiple Choice'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    num_questions = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_quiz_type_display()}) - {self.user.username}"

class UploadedFile(models.Model):
    """Model to store uploaded files"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='quiz_files/')
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename

class Question(models.Model):
    """Model to store individual questions"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    answer_text = models.TextField(blank=True)  # For flashcards
    options = models.JSONField(default=dict, blank=True)  # For multiple choice
    correct_answer = models.CharField(max_length=1, blank=True)  # For multiple choice
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Question {self.order} - {self.question_text[:50]}..."
    
    def get_options_display(self):
        """Get formatted options for display"""
        if self.quiz.quiz_type == 'multiple_choice' and self.options:
            return self.options
        return {}
    
    def is_correct(self, user_answer):
        """Check if user answer is correct"""
        if self.quiz.quiz_type == 'multiple_choice':
            return user_answer.upper() == self.correct_answer.upper()
        return False

class QuizSession(models.Model):
    """Model to track quiz sessions and user performance"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}/{self.total_questions}"
    
    def calculate_score(self):
        """Calculate percentage score"""
        if self.total_questions > 0:
            return (self.correct_answers / self.total_questions) * 100
        return 0

class UserAnswer(models.Model):
    """Model to store user answers during quiz sessions"""
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.session.user.username} - Q{self.question.order} - {'Correct' if self.is_correct else 'Incorrect'}"
