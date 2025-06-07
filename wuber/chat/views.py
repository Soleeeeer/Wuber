from django.contrib.auth import authenticate, login
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework import viewsets, permissions, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer, RegisterSerializer


def chat_page(request):
    return render(request, 'chat/chat_page.html')


@method_decorator(csrf_exempt, name='dispatch')
class SessionLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return Response({'success': 'Logged in'})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data
        chat_type = data.get('chat_type')
        participants_ids = data.get('participant_ids') or data.get('participants')
        name = data.get('name')

        if not isinstance(participants_ids, list):
            return Response({"error": "Поле 'participants' или 'participant_ids' должно быть списком"}, status=status.HTTP_400_BAD_REQUEST)

        if chat_type == Chat.PRIVATE:
            if len(participants_ids) != 1:
                return Response({"error": "Для приватного чата должен быть указан ровно один другой участник"}, status=status.HTTP_400_BAD_REQUEST)

            other_user = User.objects.filter(id=participants_ids[0]).first()
            if not other_user:
                return Response({"error": "Пользователь не найден"}, status=status.HTTP_400_BAD_REQUEST)

            existing_chats = Chat.objects.filter(
                chat_type=Chat.PRIVATE,
                participants=request.user
            ).filter(
                participants=other_user
            ).annotate(
                num_participants=Count('participants')
            ).filter(num_participants=2)

            if existing_chats.exists():
                serializer = self.get_serializer(existing_chats.first())
                return Response(serializer.data)

            chat = Chat.objects.create(chat_type=Chat.PRIVATE)
            chat.participants.add(request.user, other_user)
            chat.save()
            serializer = self.get_serializer(chat)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif chat_type == Chat.GROUP:
            if len(participants_ids) < 2:
                return Response({"error": "Для группового чата нужно минимум 2 участника"}, status=status.HTTP_400_BAD_REQUEST)

            participants = User.objects.filter(id__in=participants_ids)
            if participants.count() != len(participants_ids):
                return Response({"error": "Некоторые пользователи не найдены"}, status=status.HTTP_400_BAD_REQUEST)

            chat = Chat.objects.create(chat_type=Chat.GROUP, name=name)
            chat.participants.add(request.user)
            chat.participants.add(*participants)
            chat.save()
            serializer = self.get_serializer(chat)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({"error": "Неверный тип чата"}, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat')
        qs = Message.objects.filter(chat__participants=self.request.user)
        if chat_id:
            qs = qs.filter(chat_id=chat_id)
        return qs

    def perform_create(self, serializer):
        chat = serializer.validated_data['chat']
        if self.request.user not in chat.participants.all():
            raise PermissionDenied("Вы не участник этого чата")
        serializer.save(sender=self.request.user)


