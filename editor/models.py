from django.db import models

class CodeExecution(models.Model):
    code = models.TextField()
    language = models.CharField(max_length=10)
    output = models.TextField(blank=True)
    errors = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)