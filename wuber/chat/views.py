from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from .models import Chat, Message, ChatMembership
from .serializers import (
    ChatSerializer, MessageSerializer,
    MessageCreateSerializer, ChatMembershipSerializer, LoginSerializer
)
from django.contrib.auth.models import User
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from .models import Chat
from rest_framework.exceptions import PermissionDenied




@login_required
def chat_page(request):
    return render(request, 'chat/chat_page.html')


class SessionLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )

        if user is not None:
            login(request, user)  # создаём сессию
            return Response({'detail': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        chat = serializer.save()
        ChatMembership.objects.create(chat=chat, user=self.request.user, role='admin')

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        chat = self.get_object()
        user = get_object_or_404(User, id=request.data['user_id'])

        # Только админ может добавлять
        membership = ChatMembership.objects.filter(chat=chat, user=request.user).first()
        if not membership or membership.role != 'admin':
            return Response({'error': 'Only admin can add participants'}, status=403)

        ChatMembership.objects.create(chat=chat, user=user)
        return Response({'status': f'User {user.username} added to chat {chat.id}'})

    @action(detail=True, methods=['post'])
    def promote(self, request, pk=None):
        """Поменять роль участника"""
        chat = self.get_object()
        user = get_object_or_404(User, id=request.data['user_id'])
        role = request.data.get('role')

        if role not in ['admin', 'member']:
            return Response({'error': 'Invalid role'}, status=400)

        membership = ChatMembership.objects.filter(chat=chat, user=request.user).first()
        if not membership or membership.role != 'admin':
            return Response({'error': 'Only admin can change roles'}, status=403)

        target = ChatMembership.objects.filter(chat=chat, user=user).first()
        if target:
            target.role = role
            target.save()
            return Response({'status': f'User {user.username} role changed to {role}'})
        return Response({'error': 'User not found in chat'}, status=404)
    
    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        """Удалить участника из чата"""
        chat = self.get_object()
        user_id = request.data.get('user_id')
        target_user = get_object_or_404(User, id=user_id)

        membership = ChatMembership.objects.filter(chat=chat, user=request.user).first()
        if not membership or membership.role != 'admin':
            return Response({'error': 'Only admins can remove users'}, status=403)

        if request.user.id == target_user.id:
            return Response({'error': 'You cannot remove yourself'}, status=400)

        ChatMembership.objects.filter(chat=chat, user=target_user).delete()
        return Response({'status': f'{target_user.username} removed from chat'})
    
    def get_queryset(self):
        # Возвращаем чаты, где пользователь — участник
        return self.queryset.filter(participants=self.request.user)

    def perform_destroy(self, instance):
        # Дополнительно можно проверять, может ли пользователь удалить чат
        if not instance.participants.filter(id=self.request.user.id).exists():
            raise PermissionDenied("Вы не участник этого чата.")
        # Можно добавить проверку роли admin
        membership = instance.chatmembership_set.filter(user=self.request.user).first()
        if membership and membership.role != 'admin':
            raise PermissionDenied("Только админы могут удалять чат.")
       



class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create']:
            return MessageCreateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user:
            return Response({'error': 'You can only edit your messages'}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user:
            return Response({'error': 'You can only delete your messages'}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def forward(self, request, pk=None):
        original = self.get_object()
        chat_id = request.data.get('chat')
        chat = get_object_or_404(Chat, id=chat_id)

        forwarded = Message.objects.create(
            sender=request.user,
            chat=chat,
            content=original.content,
            forwarded_from=original
        )
        serializer = MessageSerializer(forwarded)
        return Response(serializer.data, status=201)




