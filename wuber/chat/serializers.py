from rest_framework import serializers
from .models import Chat, Message
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    content = serializers.CharField(source='text')

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'content', 'timestamp']

class ChatSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)  # для чтения участников
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        source='participants'  # связать с полем модели
    )
    messages = MessageSerializer(many=True, read_only=True)
    is_group = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'chat_type', 'name', 'is_group', 'participants', 'participant_ids', 'messages']

    def get_is_group(self, obj):
        return obj.chat_type == Chat.GROUP
