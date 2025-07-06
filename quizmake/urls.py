from django.urls import path
from . import views

urlpatterns = [
    path('', views.quizmakerhome, name='quizmakerhome'),
    path('my-quizzes/', views.my_quizzes, name='my_quizzes'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('results/<int:session_id>/', views.quiz_results, name='quiz_results'),
    path('generate-questions/', views.generate_questions_ajax, name='generate_questions_ajax'),
] 