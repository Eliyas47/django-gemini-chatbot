import os
from google import genai

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise Exception("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=API_KEY)

print("Models available:")
for m in client.models.list():
    print(m.name)
