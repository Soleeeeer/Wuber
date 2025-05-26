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
    participants = models.ManyToManyField(User, related_name='chats')
    name = models.CharField(max_length=100, blank=True, null=True)  # для групп

    def __str__(self):
        return self.name or f'Chat {self.id}'

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.text}'

