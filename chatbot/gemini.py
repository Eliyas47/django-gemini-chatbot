import google.genai as genai
from django.conf import settings

# Use GEMINI_API_KEY from settings
API_KEY = settings.GEMINI_API_KEY

if API_KEY == "TEST_KEY":
    print("⚠️ Running Gemini in test mode")
    class MockClient:
        class models:
            @staticmethod
            def generate_content(model, contents):
                class Response:
                    text = "Mock response: GEMINI_API_KEY not set."
                return Response()
    client = MockClient()
else:
    client = genai.Client(api_key=API_KEY)


def ask_gemini(history):
    conversation = "\n".join(
        f"{msg['role'].title()}: {msg['content']}" for msg in history
    )
    prompt = f"Continue this conversation:\n{conversation}\nAssistant:" if history else ""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return f"Error: {str(e)}"
