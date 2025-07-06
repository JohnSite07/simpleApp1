from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import os
import json
import logging

from .models import Quiz, UploadedFile, Question, QuizSession, UserAnswer
from .aws_utils import AWSBedrockClient, DocumentProcessor

logger = logging.getLogger(__name__)

# Create your views here.

@login_required
def quizmakerhome(request):
    """Main quiz maker page with file upload and AI generation"""
    if request.method == 'POST':
        try:
            # Get form data
            quiz_type = request.POST.get('quiz_type', 'flashcards')
            num_questions = int(request.POST.get('num_questions', 10))
            uploaded_files = request.FILES.getlist('upload_files')
            
            if not uploaded_files:
                messages.error(request, 'Please upload at least one file.')
                return render(request, 'quizmake/quizmakerhome.html')
            
            # Create quiz
            quiz = Quiz.objects.create(
                user=request.user,
                title=f"Quiz from {len(uploaded_files)} file(s)",
                quiz_type=quiz_type,
                num_questions=num_questions
            )
            
            # Process uploaded files
            all_text_content = ""
            for uploaded_file in uploaded_files:
                # Save file
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(filename)
                
                # Create UploadedFile record
                UploadedFile.objects.create(
                    quiz=quiz,
                    file=uploaded_file,
                    filename=uploaded_file.name,
                    file_size=uploaded_file.size
                )
                
                # Extract text from file
                try:
                    text_content = DocumentProcessor.extract_text_from_file(file_path)
                    all_text_content += f"\n\n--- Content from {uploaded_file.name} ---\n\n"
                    all_text_content += text_content
                except Exception as e:
                    logger.error(f"Error extracting text from {uploaded_file.name}: {e}")
                    messages.warning(request, f"Could not extract text from {uploaded_file.name}")
            
            if not all_text_content.strip():
                messages.error(request, 'No text content could be extracted from the uploaded files.')
                quiz.delete()
                return render(request, 'quizmake/quizmakerhome.html')
            
            # Generate questions using AWS Bedrock
            try:
                bedrock_client = AWSBedrockClient()
                generated_questions = bedrock_client.generate_questions(
                    all_text_content, quiz_type, num_questions
                )
                
                # Save generated questions
                for i, question_data in enumerate(generated_questions):
                    if quiz_type == 'flashcards':
                        Question.objects.create(
                            quiz=quiz,
                            question_text=question_data.get('question', ''),
                            answer_text=question_data.get('answer', ''),
                            order=i + 1
                        )
                    else:  # multiple_choice
                        Question.objects.create(
                            quiz=quiz,
                            question_text=question_data.get('question', ''),
                            options=question_data.get('options', {}),
                            correct_answer=question_data.get('correct_answer', ''),
                            order=i + 1
                        )
                
                messages.success(request, f'Successfully generated {len(generated_questions)} questions!')
                return redirect('quiz_detail', quiz_id=quiz.id)
                
            except Exception as e:
                logger.error(f"Error generating questions: {e}")
                messages.error(request, f'Failed to generate questions: {str(e)}')
                quiz.delete()
                return render(request, 'quizmake/quizmakerhome.html')
                
        except Exception as e:
            logger.error(f"Error in quiz creation: {e}")
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'quizmake/quizmakerhome.html')

@login_required
def quiz_detail(request, quiz_id):
    """Display quiz details and questions"""
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    questions = quiz.questions.all()
    
    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'quizmake/quiz_detail.html', context)

@login_required
def take_quiz(request, quiz_id):
    """Take a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    # Create or get existing session
    session, created = QuizSession.objects.get_or_create(
        quiz=quiz,
        user=request.user,
        completed_at__isnull=True,
        defaults={
            'total_questions': questions.count(),
            'correct_answers': 0
        }
    )
    
    if request.method == 'POST':
        # Handle quiz submission
        correct_count = 0
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}', '')
            is_correct = question.is_correct(user_answer)
            
            if is_correct:
                correct_count += 1
            
            UserAnswer.objects.create(
                session=session,
                question=question,
                user_answer=user_answer,
                is_correct=is_correct
            )
        
        # Update session
        session.completed_at = timezone.now()
        session.correct_answers = correct_count
        session.score = correct_count
        session.save()
        
        messages.success(request, f'Quiz completed! Score: {correct_count}/{questions.count()}')
        return redirect('quiz_results', session_id=session.id)
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'session': session,
    }
    return render(request, 'quizmake/take_quiz.html', context)

@login_required
def quiz_results(request, session_id):
    """Display quiz results"""
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)
    answers = session.answers.all().select_related('question')
    
    context = {
        'session': session,
        'answers': answers,
        'score_percentage': session.calculate_score(),
    }
    return render(request, 'quizmake/quiz_results.html', context)

@login_required
def my_quizzes(request):
    """Display user's quizzes"""
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
    }
    return render(request, 'quizmake/my_quizzes.html', context)

@csrf_exempt
def generate_questions_ajax(request):
    """AJAX endpoint for generating questions (for future use)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text_content = data.get('text_content', '')
            quiz_type = data.get('quiz_type', 'flashcards')
            num_questions = int(data.get('num_questions', 10))
            
            bedrock_client = AWSBedrockClient()
            questions = bedrock_client.generate_questions(text_content, quiz_type, num_questions)
            
            return JsonResponse({'success': True, 'questions': questions})
        except Exception as e:
            logger.error(f"Error in AJAX question generation: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
