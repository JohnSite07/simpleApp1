from django.shortcuts import render, redirect, get_object_or_404
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
            
            # Create quiz with placeholder title (will update after file processing)
            quiz = Quiz.objects.create(
                user=request.user,
                title="New Quiz", # Title will be generated from files
                quiz_type=quiz_type,
                num_questions=num_questions
            )
            
            # Process uploaded files and generate title
            all_text_content = ""
            file_names = []
            
            for uploaded_file in uploaded_files:
                # Save file using UploadedFile model (stores in quiz_files/)
                uploaded_file_instance = UploadedFile.objects.create(
                    quiz=quiz,
                    file=uploaded_file,  # This will save to 'quiz_files/' automatically
                    filename=uploaded_file.name,
                    file_size=uploaded_file.size
                )
                file_path = uploaded_file_instance.file.path
                
                # Store filename for title generation
                file_names.append(uploaded_file.name)
                
                # Extract text from file
                try:
                    text_content = DocumentProcessor.extract_text_from_file(file_path)
                    all_text_content += f"\n\n--- Content from {uploaded_file.name} ---\n\n"
                    all_text_content += text_content
                except Exception as e:
                    logger.error(f"Error extracting text from {uploaded_file.name}: {e}")
                    messages.warning(request, f"Could not extract text from {uploaded_file.name}")
            
            # Generate quiz title based on uploaded files
            if len(file_names) == 1:
                # Single file: use the filename without extension
                base_name = os.path.splitext(file_names[0])[0]
                quiz_title = f"{base_name} Quiz"
            else:
                # Multiple files: use first filename + "and X more"
                first_file = os.path.splitext(file_names[0])[0]
                if len(file_names) == 2:
                    second_file = os.path.splitext(file_names[1])[0]
                    quiz_title = f"{first_file} & {second_file} Quiz"
                else:
                    quiz_title = f"{first_file} & {len(file_names)-1} more files Quiz"
            
            # Update quiz title after all files are processed
            quiz.title = quiz_title
            quiz.save()
            
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
                
                if not generated_questions:
                    raise Exception("No questions were generated")
                
                # Save generated questions
                questions_created = 0
                for i, question_data in enumerate(generated_questions):
                    try:
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
                        questions_created += 1
                    except Exception as qe:
                        logger.warning(f"Failed to save question {i}: {qe}")
                        continue
                
                if questions_created == 0:
                    raise Exception("Failed to save any questions")
                
                messages.success(request, f'Successfully generated {questions_created} questions!')
                return redirect('quiz_detail', quiz_id=quiz.id)
                
            except Exception as e:
                logger.error(f"Error generating questions: {e}")
                error_msg = str(e)
                if "Invalid flashcard structure" in error_msg:
                    error_msg = "The AI generated questions in an invalid format. Please try again with different content or settings."
                elif "Failed to parse AI response" in error_msg:
                    error_msg = "The AI response could not be processed. Please try again."
                elif "No questions were generated" in error_msg:
                    error_msg = "No questions could be generated from the provided content. Please try with different content or fewer questions."
                else:
                    error_msg = f"Failed to generate questions: {error_msg}"
                
                messages.error(request, error_msg)
                
                # Try to create some basic questions as fallback
                try:
                    logger.info("Attempting to create fallback questions")
                    fallback_questions = []
                    if quiz_type == 'flashcards':
                        # Create simple flashcards based on file content
                        lines = all_text_content.split('\n')
                        content_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20]
                        
                        for i in range(min(5, len(content_lines), num_questions)):
                            if i < len(content_lines):
                                line = content_lines[i]
                                words = line.split()
                                if len(words) > 5:
                                    question = f"What is the main point about: {' '.join(words[:5])}..."
                                    answer = line[:100] + "..." if len(line) > 100 else line
                                    
                                    Question.objects.create(
                                        quiz=quiz,
                                        question_text=question,
                                        answer_text=answer,
                                        order=i + 1
                                    )
                                    fallback_questions.append(i + 1)
                    else:
                        # Create simple multiple choice questions
                        for i in range(min(3, num_questions)):
                            Question.objects.create(
                                quiz=quiz,
                                question_text=f"Question {i+1} about the uploaded content",
                                options={
                                    "A": "Option A",
                                    "B": "Option B", 
                                    "C": "Option C",
                                    "D": "Option D"
                                },
                                correct_answer="A",
                                order=i + 1
                            )
                            fallback_questions.append(i + 1)
                    
                    if fallback_questions:
                        messages.warning(request, f'AI generation failed, but created {len(fallback_questions)} basic questions as fallback. You can edit them later.')
                        return redirect('quiz_detail', quiz_id=quiz.id)
                    else:
                        quiz.delete()
                        return render(request, 'quizmake/quizmakerhome.html')
                        
                except Exception as fallback_error:
                    logger.error(f"Fallback question creation also failed: {fallback_error}")
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

@login_required
def delete_quiz(request, quiz_id):
    """Delete a quiz and its associated files (files deleted via model signals)"""
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # Store quiz title for confirmation message
            quiz_title = quiz.title
            
            # Delete the quiz (this will cascade delete related objects and files via signals)
            quiz.delete()
            
            messages.success(request, f'Quiz "{quiz_title}" has been deleted successfully.')
            return redirect('my_quizzes')
            
        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            messages.error(request, f'Failed to delete quiz: {str(e)}')
            return redirect('my_quizzes')
    
    # If not POST, redirect to my_quizzes
    return redirect('my_quizzes')

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
