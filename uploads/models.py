from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name