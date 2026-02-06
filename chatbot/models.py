from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Conversation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    summary = models.TextField(blank=True, null=True)
    total_messages = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
        
    )

    ROLE_CHOICES = [
        ("user", "User"),
        ("model", "Model"),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # Make content optional (because file upload may not have text)
    content = models.TextField(blank=True, null=True)

    # NEW: File field
    file = models.FileField(
        upload_to="chat_files/",
        blank=True,
        null=True
    )

    timestamp = models.DateTimeField(default=timezone.now)
    file = models.FileField(upload_to="chat_files/", null=True, blank=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        if self.content:
            return f"{self.conversation.title} ({self.role})"
        return f"{self.conversation.title} ({self.role} - file)"
