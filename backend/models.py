# models.py
from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]
    
    id = models.CharField(max_length=100, primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey(User, related_name="updated_tasks", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    user_id = models.CharField(max_length=100)  # Fallback for unauthenticated users
    username = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["room", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.username}: {self.message[:50]}"
