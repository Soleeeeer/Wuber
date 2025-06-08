from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    PRIVATE = 'private'
    GROUP = 'group'
    CHAT_TYPE_CHOICES = [
        (PRIVATE, 'Private'),
        (GROUP, 'Group'),
    ]

    chat_type = models.CharField(max_length=10, choices=CHAT_TYPE_CHOICES)
    name = models.CharField(max_length=100, blank=True, null=True)  # для групп
    participants = models.ManyToManyField(User, through='ChatMembership', related_name='chats')

    def __str__(self):
        return self.name or f"Chat {self.id}"

class ChatMembership(models.Model):
    ADMIN = 'admin'
    MEMBER = 'member'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MEMBER, 'Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)

    class Meta:
        unique_together = ('user', 'chat')

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    forwarded_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Message {self.id} in Chat {self.chat_id}"
