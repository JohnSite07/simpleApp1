import boto3
import json
import os
from django.conf import settings
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

class AWSBedrockClient:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.model_id = settings.AWS_BEDROCK_MODEL
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Bedrock client with credentials from environment variables/settings"""
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=self.region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            logger.info("AWS Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {e}")
            raise
    
    def generate_questions(self, text_content, quiz_type, num_questions):
        """Generate questions using AWS Bedrock"""
        try:
            prompt = self._create_prompt(text_content, quiz_type, num_questions)
            
            # Use the correct format for Claude 3
            if 'claude' in self.model_id.lower():
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        'anthropic_version': 'bedrock-2023-05-31',
                        'max_tokens': 4000,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'messages': [
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ]
                    })
                )
                
                response_body = json.loads(response['body'].read())
                generated_text = response_body.get('content', [{}])[0].get('text', '')
            else:
                # Fallback for other models
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        'prompt': prompt,
                        'max_tokens': 4000,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'stop_sequences': ['\n\nHuman:', '\n\nAssistant:']
                    })
                )
                
                response_body = json.loads(response['body'].read())
                generated_text = response_body.get('completion', '')
            
            return self._parse_questions(generated_text, quiz_type)
            
        except ClientError as e:
            logger.error(f"AWS Bedrock API error: {e}")
            raise Exception(f"Failed to generate questions: {e}")
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            raise
    
    def _create_prompt(self, text_content, quiz_type, num_questions):
        """Create a prompt for question generation"""
        if quiz_type == 'flashcards':
            prompt_template = f"""You are an expert educator creating flashcards from educational content. Based on the following text, create exactly {num_questions} high-quality flashcards.

Text content:
{text_content[:8000]}

Instructions:
1. Create exactly {num_questions} flashcards
2. Each flashcard should have a clear question on the front and a concise answer on the back
3. Focus on key concepts, definitions, important facts, and main ideas
4. Make questions that test understanding, not just memorization
5. Keep answers concise but complete
6. Ensure questions are relevant to the provided content

IMPORTANT: You must respond with ONLY valid JSON. Do not include any other text before or after the JSON.

Format your response as valid JSON only:
{{
    "flashcards": [
        {{
            "question": "Question text here",
            "answer": "Answer text here"
        }}
    ]
}}

Generate the flashcards now:"""
        else:  # multiple_choice
            prompt_template = f"""You are an expert educator creating multiple choice questions from educational content. Based on the following text, create exactly {num_questions} high-quality multiple choice questions.

Text content:
{text_content[:8000]}

Instructions:
1. Create exactly {num_questions} multiple choice questions
2. Each question should have 4 options (A, B, C, D)
3. Only one option should be correct
4. Focus on key concepts, definitions, important facts, and main ideas
5. Make questions that test understanding, not just memorization
6. Ensure all distractors (wrong answers) are plausible
7. Ensure questions are relevant to the provided content

IMPORTANT: You must respond with ONLY valid JSON. Do not include any other text before or after the JSON.

Format your response as valid JSON only:
{{
    "questions": [
        {{
            "question": "Question text here",
            "options": {{
                "A": "Option A",
                "B": "Option B", 
                "C": "Option C",
                "D": "Option D"
            }},
            "correct_answer": "A"
        }}
    ]
}}

Generate the questions now:"""
        return prompt_template
    
    def _parse_questions(self, generated_text, quiz_type):
        """Parse the generated text into structured question data"""
        try:
            # Clean the response text
            generated_text = generated_text.strip()
            
            # Try to find JSON in the response
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # If no JSON found, try to extract from markdown code blocks
                if '```json' in generated_text:
                    start = generated_text.find('```json') + 7
                    end = generated_text.find('```', start)
                    if end != -1:
                        json_str = generated_text[start:end].strip()
                    else:
                        raise ValueError("No JSON found in response")
                elif '```' in generated_text:
                    # Try to extract from any code block
                    start = generated_text.find('```') + 3
                    end = generated_text.find('```', start)
                    if end != -1:
                        json_str = generated_text[start:end].strip()
                    else:
                        raise ValueError("No JSON found in response")
                else:
                    raise ValueError("No JSON found in response")
            else:
                json_str = generated_text[json_start:json_end]
            
            # Parse JSON
            data = json.loads(json_str)
            
            if quiz_type == 'flashcards':
                flashcards = data.get('flashcards', [])
                # Validate flashcards structure
                for flashcard in flashcards:
                    if not flashcard.get('question') or not flashcard.get('answer'):
                        raise ValueError("Invalid flashcard structure")
                return flashcards
            else:
                questions = data.get('questions', [])
                # Validate questions structure
                for question in questions:
                    if not question.get('question') or not question.get('options') or not question.get('correct_answer'):
                        raise ValueError("Invalid question structure")
                return questions
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Generated text: {generated_text}")
            raise Exception("Failed to parse AI response - invalid JSON format")
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            raise

class DocumentProcessor:
    """Handle document processing and text extraction"""
    
    @staticmethod
    def extract_text_from_file(file_path):
        """Extract text from various file types"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension in ['.txt', '.md']:
                return DocumentProcessor._extract_text_plain(file_path)
            elif file_extension in ['.pdf']:
                return DocumentProcessor._extract_text_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return DocumentProcessor._extract_text_docx(file_path)
            elif file_extension in ['.pptx', '.ppt']:
                return DocumentProcessor._extract_text_pptx(file_path)
            else:
                # For unsupported file types, try to extract as plain text
                return DocumentProcessor._extract_text_plain(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    @staticmethod
    def _extract_text_plain(file_path):
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    @staticmethod
    def _extract_text_pdf(file_path):
        """Extract text from PDF files"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.warning("PyPDF2 not installed, treating PDF as plain text")
            return DocumentProcessor._extract_text_plain(file_path)
    
    @staticmethod
    def _extract_text_docx(file_path):
        """Extract text from DOCX files"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx not installed, treating DOCX as plain text")
            return DocumentProcessor._extract_text_plain(file_path)
    
    @staticmethod
    def _extract_text_pptx(file_path):
        """Extract text from PPTX files"""
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text
        except ImportError:
            logger.warning("python-pptx not installed, treating PPTX as plain text")
            return DocumentProcessor._extract_text_plain(file_path) 