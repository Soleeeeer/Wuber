from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import chat_page, RegisterView, SessionLoginView, ChatViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('chat/', chat_page, name='chat_page'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/session-login/', SessionLoginView.as_view(), name='session_login'),
    path('api/', include(router.urls)),  # <--- Подключаем маршруты для ViewSet
]
