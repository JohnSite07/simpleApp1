from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os
import logging

from .models import Quiz, UploadedFile

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=Quiz)
def delete_quiz_files(sender, instance, **kwargs):
    """Delete uploaded files when a quiz is deleted"""
    try:
        # Get all uploaded files for this quiz
        uploaded_files = instance.uploaded_files.all()
        
        for uploaded_file in uploaded_files:
            try:
                if uploaded_file.file:
                    # Get the file path and delete the file
                    file_path = uploaded_file.file.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted file via signal: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {uploaded_file.filename} via signal: {e}")
                
    except Exception as e:
        logger.error(f"Error in delete_quiz_files signal for quiz {instance.id}: {e}")

@receiver(pre_delete, sender=UploadedFile)
def delete_uploaded_file(sender, instance, **kwargs):
    """Delete the physical file when an UploadedFile is deleted"""
    try:
        if instance.file:
            # Get the file path and delete the file
            file_path = instance.file.path
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted uploaded file via signal: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting uploaded file {instance.filename} via signal: {e}") 