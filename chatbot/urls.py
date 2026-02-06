from django.urls import path
from .views import (
    FileUploadChatView,
    chat,
    chat_stream,
    delete_conversation,
    login,
    regenerate_response,
    register,
    create_conversation,
    list_conversations,
    get_conversation_messages,
    chat_info,
    rename_conversation
)

urlpatterns = [
    path("chat/", chat),
    path("login/", login),
    path("register/", register),
    path("info/", chat_info),
    path("conversations/create/", create_conversation),
    path("conversations/", list_conversations),
    path("conversations/<int:conversation_id>/messages/", get_conversation_messages),
    path("conversations/<int:conversation_id>/delete/", delete_conversation),
    path("conversations/<int:conversation_id>/rename/", rename_conversation),
    path("chat/regenerate/", regenerate_response),
    path("chat/stream/", chat_stream),
    path("chat/upload/", FileUploadChatView.as_view(), name="chat-upload")

]

