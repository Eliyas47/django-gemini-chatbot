from django.urls import path
from .views import (
    chat,
    login,
    register,
    chat_info,
    debug_context
)

urlpatterns = [
    path("chat/", chat),
    path("login/", login),
    path("register/", register),
    path("info/", chat_info),
    path("debug-context/", debug_context),
]
