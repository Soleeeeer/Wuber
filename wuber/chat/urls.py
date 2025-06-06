from django.urls import path
from . import views
from .views import chat_page
from chat.views import RegisterView


urlpatterns = [
    path('chat/', chat_page, name='chat_page'),
    path('api/register/', RegisterView.as_view(), name='register'),
]
