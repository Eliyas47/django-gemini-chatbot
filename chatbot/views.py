from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from datetime import datetime

from .models import Conversation, ChatMessage
from .gemini import ask_gemini


# ----------------------------------------
# INFO
# ----------------------------------------
@api_view(['GET'])
def chat_info(request):
    return Response({
        "detail": "Use POST /api/chat/ with {message, conversation_id}"
    })


# ----------------------------------------
# REGISTER
# ----------------------------------------
@api_view(['POST'])
def register(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    return Response({"message": "User created"}, status=201)


# ----------------------------------------
# LOGIN
# ----------------------------------------
@api_view(['POST'])
def login(request):
    user = authenticate(
        username=request.data.get("username"),
        password=request.data.get("password")
    )

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key})


# ----------------------------------------
# CREATE CONVERSATION
# ----------------------------------------
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    title = request.data.get("title", "New Chat")

    conversation = Conversation.objects.create(
        user=request.user,
        title=title
    )

    return Response({
        "conversation_id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at
    })


# ----------------------------------------
# LIST USER CONVERSATIONS
# ----------------------------------------
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    conversations = Conversation.objects.filter(user=request.user)

    data = [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at
        }
        for c in conversations
    ]

    return Response({
        "user": request.user.username,
        "conversations": data
    })


# ----------------------------------------
# CHAT (SEND MESSAGE)
# ----------------------------------------
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chat(request):
    message = request.data.get("message")
    conversation_id = request.data.get("conversation_id")

    if not message:
        return Response({"error": "Message is required"}, status=400)

    if not conversation_id:
        return Response({"error": "conversation_id is required"}, status=400)

    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            user=request.user
        )
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    # Save user message
    ChatMessage.objects.create(
        conversation=conversation,
        role="user",
        content=message
    )

    # If this is the FIRST user message → generate short title
    if conversation.messages.filter(role="user").count() == 1:

        title_prompt = [
            {
                "role": "user",
                "content": f"Summarize this into a very short 4-6 word conversation title only:\n\n{message}"
            }
        ]

        short_title = ask_gemini(title_prompt)

        if short_title.startswith("Error"):
            short_title = message[:40]

        clean_title = short_title.strip()
        clean_title = clean_title.replace('"', '')
        clean_title = clean_title.replace('*', '')
        clean_title = clean_title.replace('\n', '')

        conversation.title = clean_title[:60]
        conversation.save()

    # Get last 20 messages
    messages = ChatMessage.objects.filter(
        conversation=conversation
    ).order_by("timestamp")[:20]

    history = [
        {"role": m.role, 
         "content": m.content}
        for m in messages
    ]

    # Ask Gemini for reply
    ai_response = ask_gemini(history)

    if ai_response.startswith("Error"):
        return Response({"error": ai_response}, status=502)

    # Save AI reply
    ChatMessage.objects.create(
        conversation=conversation,
        role="model",
        content=ai_response
    )

    return Response({
        "conversation_id": conversation.id,
        "user_message": message,
        "ai_response": ai_response,
        "timestamp": datetime.utcnow(),
        "history_length": len(history)
    })



# ----------------------------------------
# GET MESSAGES FROM A CONVERSATION
# ----------------------------------------
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):

    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            user=request.user
        )
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    messages = ChatMessage.objects.filter(
        conversation=conversation
    ).order_by("timestamp")

    data = [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp
        }
        for m in messages
    ]

    return Response({
        "conversation_id": conversation.id,
        "title": conversation.title,
        "total_messages": len(data),
        "messages": data
    })
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            user=request.user
        )
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    conversation.delete()

    return Response({"message": "Conversation deleted successfully"})
@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def rename_conversation(request, conversation_id):
    new_title = request.data.get("title")

    if not new_title:
        return Response({"error": "Title is required"}, status=400)

    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            user=request.user
        )
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    conversation.title = new_title[:60]
    conversation.save()

    return Response({
        "message": "Title updated",
        "conversation_id": conversation.id,
        "new_title": conversation.title
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    search_query = request.GET.get("search")

    conversations = Conversation.objects.filter(user=request.user)

    if search_query:
        conversations = conversations.filter(title__icontains=search_query)

    conversations = conversations.order_by("-created_at")

    data = [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at
        }
        for c in conversations
    ]

    return Response({
        "user": request.user.username,
        "total": len(data),
        "conversations": data
    })

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def regenerate_response(request):
    conversation_id = request.data.get("conversation_id")

    if not conversation_id:
        return Response({"error": "conversation_id is required"}, status=400)

    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            user=request.user
        )
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    # Delete last AI message
    last_ai_message = ChatMessage.objects.filter(
        conversation=conversation,
        role="model"
    ).order_by("-timestamp").first()

    if last_ai_message:
        last_ai_message.delete()

    # Get history again
    messages = ChatMessage.objects.filter(
        conversation=conversation
    ).order_by("timestamp")[:20]

    history = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]

    ai_response = ask_gemini(history)

    if ai_response.startswith("Error"):
        return Response({"error": ai_response}, status=502)

    ChatMessage.objects.create(
        conversation=conversation,
        role="model",
        content=ai_response
    )

    return Response({
        "conversation_id": conversation.id,
        "new_ai_response": ai_response
    })
