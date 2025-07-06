# QuizMaker App

An AI-powered quiz generation application that creates personalized quizzes and flashcards from uploaded documents using AWS Bedrock.

## Features

- **Document Upload**: Support for PDF, PPTX, DOCX, TXT, and many other formats
- **AI-Powered Generation**: Uses AWS Bedrock (Claude 3) to generate questions
- **Two Quiz Types**: 
  - Flashcards: Question and answer pairs
  - Multiple Choice: Questions with 4 answer options
- **User Management**: Track quiz sessions and performance
- **Responsive Design**: Modern, mobile-friendly interface

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. AWS Configuration

Create a `.env` file in your project root with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

### 3. Required AWS Permissions

Your AWS user/role needs the following permissions:
- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`

### 4. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

## Usage

1. **Create Quiz**: Upload documents and select quiz type
2. **AI Processing**: The app extracts text and generates questions
3. **Take Quiz**: Practice with generated questions
4. **Track Progress**: View results and performance

## File Support

The app can process various file formats:
- **Text**: PDF, DOCX, PPTX, TXT, MD
- **Images**: JPG, PNG, GIF, BMP, SVG, WEBP
- **Office**: ODT, ODP, XLS, XLSX, CSV, RTF
- **Web**: HTML, HTM
- **Archives**: ZIP, RAR, 7Z, TAR, GZ
- **Media**: MP3, MP4, AVI, MOV, MKV, WAV, FLAC, OGG
- **Data**: JSON, XML
- **E-books**: EPUB, MOBI, AZW3
- **Graphics**: CBZ, CBR, XPS, PS, TEX, PSD, AI, INDD
- **CAD**: DWG, DXF, SKP, BLEND, FBX, OBJ, STL, 3DS, DAE, PLY, GLTF, GLB, USDZ, IGES, STEP, STP, SLDPRT, SLDASM, PRT, ASM, CATPART, CATPRODUCT

## API Endpoints

- `GET /quizmake/` - Quiz creation page
- `POST /quizmake/` - Create new quiz
- `GET /quizmake/my-quizzes/` - User's quizzes
- `GET /quizmake/quiz/<id>/` - Quiz details
- `GET /quizmake/quiz/<id>/take/` - Take quiz
- `POST /quizmake/quiz/<id>/take/` - Submit quiz answers
- `GET /quizmake/results/<id>/` - Quiz results

## Models

- **Quiz**: Main quiz information
- **UploadedFile**: Document files
- **Question**: Individual questions
- **QuizSession**: User quiz sessions
- **UserAnswer**: User responses

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure your AWS credentials are properly configured
2. **File Processing**: Some file types may require additional libraries
3. **Token Limits**: Large documents are truncated to 8000 characters
4. **JSON Parsing**: AI responses must be valid JSON format

### Error Handling

The app includes comprehensive error handling for:
- File upload failures
- Text extraction errors
- AWS API errors
- JSON parsing issues
- Database errors

## Development

### Adding New File Types

To add support for new file types, modify the `DocumentProcessor` class in `aws_utils.py`.

### Customizing AI Prompts

Edit the `_create_prompt` method in `AWSBedrockClient` to customize question generation.

### Styling

The app uses Tailwind CSS for styling. Templates are located in `templates/quizmake/`. 