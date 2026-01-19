# chatbot/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone  # Add this import

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    role = models.CharField(max_length=10)  # "user" or "model"
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add=True
    
    class Meta:
        ordering = ['timestamp']  # Ensure consistent ordering
    
    def __str__(self):
        return f"{self.user.username} ({self.role}): {self.content[:50]}"