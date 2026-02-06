import os
from google import genai
from google.genai import types
from django.conf import settings


# Initialize client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


# ==============================
# 1️⃣ Normal Response Function
# ==============================
def ask_gemini(messages, temperature=0.7):
    try:
        model_id = "gemini-2.5-flash"

        formatted_contents = [
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])]
            )
            for msg in messages
        ]

        response = client.models.generate_content(
            model=model_id,
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                temperature=temperature
            )
        )

        return response.text

    except Exception as e:
        return f"Error: {str(e)}"


# ==============================
# 2️⃣ Streaming Response Function
# ==============================
def ask_gemini_stream(messages, temperature=0.7):
    try:
        model_id = "gemini-2.5-flash"

        formatted_contents = [
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])]
            )
            for msg in messages
        ]

        stream = client.models.generate_content_stream(
            model=model_id,
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                temperature=temperature
            )
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"Error: {str(e)}"


# ==============================
# 3️⃣ File Analysis Function (NEW)
# ==============================
def ask_gemini_file(file_bytes, prompt):
    try:
        model_id = "gemini-2.5-flash" # Use a valid model ID

        response = client.models.generate_content(
            model=model_id,
            # ADD THIS CONFIG BLOCK
            config=types.GenerateContentConfig(
                system_instruction="Reply in plain text only. Do not use markdown formatting like **bold** or *italics*."
            ),
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=file_bytes,
                            mime_type="application/pdf"
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
    
def summarize_conversation(messages):
    prompt = [
        {
            "role": "user",
            "content": f"""
Summarize this conversation briefly to preserve memory context.
Focus on key topics and decisions only.

Conversation:
{messages}
"""
        }
    ]

    return ask_gemini(prompt)
