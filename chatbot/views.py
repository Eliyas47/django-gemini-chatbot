from functools import cache
from pyexpat.errors import messages
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
from django.http import StreamingHttpResponse
from .gemini import ask_gemini_stream
from rest_framework.views import APIView
from rest_framework import serializers


from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from django.http import StreamingHttpResponse
from .gemini import ask_gemini_stream
import json

# ----------------------------------------
# INFO
# ----------------------------------------
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def chat_info(request):
    return Response({
        "detail": "Use POST /api/chat/ with {message, conversation_id}"
    })


# ----------------------------------------
# REGISTER
# ----------------------------------------
@api_view(['POST'])
@authentication_classes([])   # disable authentication
@permission_classes([AllowAny])
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
@authentication_classes([])
@permission_classes([AllowAny])
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
    # 1. Get initial data
    message = request.data.get("message")
    conversation_id = request.data.get("conversation_id")
    file = request.FILES.get("file") # Handling files if needed

    # 2. Basic Validation
    if not message:
        return Response({"error": "Message is required"}, status=400)
    if not conversation_id:
        return Response({"error": "conversation_id is required"}, status=400)

    # 3. Retrieve Conversation (and verify owner)
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    # 4. Save User Message
    ChatMessage.objects.create(
        conversation=conversation,
        role="user",
        content=message
    )
    

    # 5. Get AI Response (using your gemini.py function)
    # We fetch history to provide context to the AI
    history = list(conversation.messages.values('role', 'content'))
    ai_response = ask_gemini(history) 

    # 6. Update Token Count & Stats
    # Note: len(split) is an estimate. Gemini API usage_metadata is more accurate.
    conversation.total_tokens += len(ai_response.split())
    
    # 7. Generate Title for new conversations
    if conversation.messages.filter(role="user").count() == 1:
        title_prompt = [{"role": "user", "content": f"Summarize this into 4-6 words title only: {message}"}]
        short_title = ask_gemini(title_prompt)
        
        # Clean the title
        clean_title = short_title.replace('"', '').replace('*', '').replace('\n', '').strip()
        conversation.title = clean_title[:60]
    
    conversation.save()

    # 8. Save AI Message
    ChatMessage.objects.create(
        conversation=conversation,
        role="model",
        content=ai_response
    )
    user_key = f"rate_limit_{request.user.id}"
    request_count = cache.get(user_key, 0)

    if request_count > 50:
         return Response({"error": "Daily limit reached"}, status=429)

    cache.set(user_key, request_count + 1, timeout=86400)

    # 🧠 9. Auto-Summarize (Memory Compression)
    if conversation.messages.count() > 30:
        # Get the oldest 20 messages
        old_messages = conversation.messages.order_by("timestamp")[:20]
        
        summary_text = "\n".join([f"{m.role}: {m.content}" for m in old_messages])
        summary_prompt = [{"role": "user", "content": f"Summarize this chat history for memory:\n\n{summary_text}"}]
        
        summary = ask_gemini(summary_prompt)

        # Create a special system/model message for the summary
        ChatMessage.objects.create(
            conversation=conversation,
            role="model",
            content=f"[Memory Summary]: {summary}"
        )

        # Delete old messages to free up DB space and context window
        ChatMessage.objects.filter(id__in=[m.id for m in old_messages]).delete()

    return Response({"message": ai_response, "title": conversation.title})    # Get last 20 messages
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

# ----------------------------------------
# STREAMING CHAT (POST /api/chat/stream)
# ----------------------------------------
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from .gemini import ask_gemini_stream
import json

# Authenticated streaming chat
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chat_stream(request):
    message = request.data.get("message")
    conversation_id = request.data.get("conversation_id")

    if not message:
        return Response({"error": "Message is required"}, status=400)
    if not conversation_id:
        return Response({"error": "conversation_id is required"}, status=400)

    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    # Save user message
    ChatMessage.objects.create(
        conversation=conversation,
        role="user",
        content=message
    )

    # Fetch last 20 messages for context
    messages = ChatMessage.objects.filter(conversation=conversation).order_by("timestamp")[:20]
    history = [{"role": m.role, "content": m.content} for m in messages]

    # Streaming generator
    def stream():
        full_response = ""
        for chunk in ask_gemini_stream(history):
            full_response += chunk
            yield chunk
        # Save AI response after streaming finishes
        ChatMessage.objects.create(
            conversation=conversation,
            role="model",
            content=full_response
        )

    response = StreamingHttpResponse(stream(), content_type='text/plain')
    response['X-Accel-Buffering'] = 'no'  # Optional: disable buffering for immediate streaming
    return response


# Public unauthenticated streaming endpoint
@api_view(['POST'])
@authentication_classes([])  # No auth
@permission_classes([AllowAny])
def chat_stream_public(request):
    """
    Example endpoint for testing streaming without auth (Postman-friendly)
    """
    try:
        data = json.loads(request.body)
    except Exception:
        return Response({"error": "Invalid JSON"}, status=400)

    message = data.get("message")
    if not message:
        return Response({"error": "Message is required"}, status=400)

    messages = [{"role": "user", "content": message}]

    response = StreamingHttpResponse(
        ask_gemini_stream(messages),
        content_type='text/plain'
    )
    response['X-Accel-Buffering'] = 'no'
    return response


import os
from google import genai
from google.genai import types  # <--- Essential for file bytes
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.cache import cache

class FileUploadChatView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        file = request.FILES.get("file")
        prompt = request.data.get("prompt", "Analyze this file.")

        if not file or not conversation_id:
            return Response({"error": "file and conversation_id are required"}, status=400)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

        # 1. MIME TYPE FIXER logic
        # Gemini is picky about 'application/msword'. 
        # We try to detect if it's a type Gemini likes, otherwise we fallback.
        supported_types = [
            'application/pdf', 'image/jpeg', 'image/png', 
            'image/webp', 'text/plain', 'application/json',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document' # .docx
        ]
        
        mime_type = file.content_type
        
        # If it's a known problematic type like .doc, we warn the user or try text/plain
        if mime_type == 'application/msword':
            return Response({
                "error": "Gemini does not support old .doc files. Please save as .pdf or .docx"
            }, status=400)

        # 2. Save User Message
        user_msg = ChatMessage.objects.create(
            conversation=conversation,
            role="user",
            content=prompt,
            file=file
        )

        try:
            # 3. Initialize Gemini Client
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            file.seek(0)
            file_bytes = file.read()

            # 4. Request Analysis
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type
                    )
                ]
            )
            
            ai_text = response.text

            # 5. Save AI response
            ChatMessage.objects.create(
                conversation=conversation,
                role="model",
                content=ai_text
            )

            return Response({"analysis": ai_text})

        except Exception as e:
            return Response({"error": f"AI Processing Error: {str(e)}"}, status=500)
class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"




@api_view(['POST'])
@authentication_classes([]) # Disable authentication for this view
@permission_classes([AllowAny]) # Allow anyone to access
def chat_stream_view(request):
    data = json.loads(request.body)
    message = data.get("message", "")
    
    # We pass the list of messages to our gemini function
    messages = [{"role": "user", "content": message}]
    
    response = StreamingHttpResponse(
        ask_gemini_stream(messages), 
        content_type='text/plain'
    )
    return response