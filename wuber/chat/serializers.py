from rest_framework import serializers
from .models import Chat, Message, ChatMembership
from django.contrib.auth.models import User
from rest_framework.serializers import ModelSerializer, Serializer, CharField


class LoginSerializer(Serializer):
    username = CharField(required=True)
    password = CharField(required=True, write_only=True)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ChatSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'chat_type', 'name', 'participants']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    forwarded_from = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'content', 'created_at', 'updated_at', 'forwarded_from']

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['chat', 'content', 'forwarded_from']

class ChatMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = ChatMembership
        fields = ['user', 'chat', 'role']

