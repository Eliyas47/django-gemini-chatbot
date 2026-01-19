# views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from datetime import datetime

from .gemini import ask_gemini
from .models import ChatMessage


@api_view(['GET'])
def chat_info(request):
    return Response({
        "detail": "POST /api/chat/ with JSON: {'message': 'Hello'}"
    })


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


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chat(request):
    message = request.data.get("message")
    if not message:
        return Response({"error": "Message is required"}, status=400)

    user = request.user

    # Save user message
    ChatMessage.objects.create(
        user=user,
        role="user",
        content=message
    )

    # Get messages in correct order (oldest to newest)
    past_messages = ChatMessage.objects.filter(
        user=user
    ).order_by("timestamp")[:20]

    history = [
        {"role": m.role, "content": m.content}
        for m in past_messages
    ]

    # Make sure we have the current message in history
    if not history or history[-1]["content"] != message:
        history.append({"role": "user", "content": message})

    ai_response = ask_gemini(history)

    # If Gemini failed
    if ai_response.startswith("Gemini API Error"):
        return Response({"error": ai_response}, status=502)

    # Save AI response
    ChatMessage.objects.create(
        user=user,
        role="model",
        content=ai_response
    )

    return Response({
        "user_message": message,
        "ai_response": ai_response,
        "timestamp": datetime.utcnow(),
        "history_length": len(history)
    })


# Debug view to check context
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def debug_context(request):
    """Debug endpoint to see what context is being sent"""
    user = request.user
    past_messages = ChatMessage.objects.filter(
        user=user
    ).order_by("timestamp")[:20]
    
    history = [
        {"role": m.role, "content": m.content}
        for m in past_messages
    ]
    
    return Response({
        "user": user.username,
        "total_messages": ChatMessage.objects.filter(user=user).count(),
        "context_messages": len(history),
        "history": history
    })