from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer, RegisterSerializer
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from django.contrib.auth.models import User

@login_required
def chat_page(request):
    return render(request, 'chat.html')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return user.chats.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        chat_type = data.get('chat_type')
        participants_ids = data.get('participants')  # ожидаем список id пользователей
        name = data.get('name')

        if chat_type == Chat.PRIVATE:
            if not participants_ids or len(participants_ids) != 1:
                return Response({"error": "Для приватного чата должен быть указан ровно один другой участник"}, status=status.HTTP_400_BAD_REQUEST)

            other_user_id = participants_ids[0]
            other_user = User.objects.filter(id=other_user_id).first()
            if not other_user:
                return Response({"error": "Пользователь не найден"}, status=status.HTTP_400_BAD_REQUEST)

            # Проверка, есть ли уже чат между этими двумя пользователями
            existing_chats = Chat.objects.filter(chat_type=Chat.PRIVATE, participants=request.user).filter(participants=other_user)
            if existing_chats.exists():
                return Response(ChatSerializer(existing_chats.first()).data)

            chat = Chat.objects.create(chat_type=Chat.PRIVATE)
            chat.participants.add(request.user, other_user)
            chat.save()
            serializer = self.get_serializer(chat)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif chat_type == Chat.GROUP:
            if not participants_ids or len(participants_ids) < 2:
                return Response({"error": "Для группового чата нужно минимум 2 участника"}, status=status.HTTP_400_BAD_REQUEST)
            
            chat = Chat.objects.create(chat_type=Chat.GROUP, name=name)
            chat.participants.add(request.user)
            participants = User.objects.filter(id__in=participants_ids)
            chat.participants.add(*participants)
            chat.save()
            serializer = self.get_serializer(chat)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response({"error": "Неверный тип чата"}, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(chat__participants=user)

    def perform_create(self, serializer):
        chat = serializer.validated_data['chat']
        if self.request.user not in chat.participants.all():
            raise PermissionDenied("Вы не участник этого чата")
        serializer.save(sender=self.request.user)



