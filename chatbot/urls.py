# chatbot/urls.py
from django.urls import path
from .views import chat, register, login, chat_info, debug_context  # Changed from debug_auth to debug_context

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('chat/info/', chat_info, name='chat_info'),
    path('chat/debug/', debug_context, name='debug_context'),  # Changed here
    path('register/', register, name='register'),
    path('login/', login, name='login'),
]