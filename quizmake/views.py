from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

# Create your views here.

def quizmakerhome(request):
    uploaded_files = []
    if request.method == 'POST' and request.FILES.getlist('upload_files'):
        files = request.FILES.getlist('upload_files')
        fs = FileSystemStorage()
        for f in files:
            filename = fs.save(f.name, f)
            uploaded_files.append(filename)
    return render(request, 'quizmake/quizmakerhome.html', {'uploaded_files': uploaded_files})
