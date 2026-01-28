# django-gemini-chatbot

Local development setup

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv venv
& .\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```
Here is a complete professional **README.md** for your Django Gemini Chatbot project.

You can copy this directly into your `README.md` file.

---

# 🧠 Django Gemini Chatbot API

A ChatGPT-like backend built with **Django REST Framework + Gemini AI**, supporting:

* 🔐 Token Authentication
* 💬 Multi-conversation chat history
* 🧠 AI-generated responses
* 🏷️ Auto-generated conversation titles
* 🔍 Search conversations
* ✏️ Rename conversations
* 🗑️ Delete conversations
* 🔁 Regenerate AI response

---

# 🚀 Features

### ✅ Authentication

* User registration
* Login with token authentication
* Protected API endpoints

### ✅ Conversations

* Create multiple conversations
* AI auto-generates short titles from first message
* List user conversations
* Search conversations by title
* Rename conversations
* Delete conversations

### ✅ Chat System

* Stores full message history
* Sends last 20 messages to Gemini
* Saves both user + AI messages
* Regenerate last AI response

---

# 🏗️ Tech Stack

* Python 3.11
* Django 5
* Django REST Framework
* DRF Token Authentication
* SQLite
* Google Gemini API

---

# 📂 Project Structure

```
django-gemini-chatbot/
│
├── backend/
│   └── settings.py
│   └── urls.py
│
├── chatbot/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── gemini.py
│   └── migrations/
│
├── manage.py
└── db.sqlite3
```

---

# ⚙️ Installation Guide

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/django-gemini-chatbot.git
cd django-gemini-chatbot
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3️⃣ Install Requirements

```bash
pip install django djangorestframework djangorestframework-simplejwt google-generativeai
```

---

## 4️⃣ Add Gemini API Key

Inside `chatbot/gemini.py`:

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")
```

---

## 5️⃣ Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 6️⃣ Run Server

```bash
python manage.py runserver
```

Server runs at:

```
http://127.0.0.1:8000/
```

---

# 🔑 Authentication Flow

### 1. Register

POST

```
/api/register/
```

Body:

```json
{
  "username": "testuser",
  "password": "123456"
}
```

---

### 2. Login

POST

```
/api/login/
```

Response:

```json
{
  "token": "abc123xyz..."
}
```

Use this token in all protected endpoints:

Header:

```
Authorization: Token abc123xyz...
```

---

# 💬 API Endpoints

## 🔹 Create Conversation

POST

```
/api/conversations/create/
```

---

## 🔹 List Conversations

GET

```
/api/conversations/
```

Search:

```
/api/conversations/?search=django
```

---

## 🔹 Send Chat Message

POST

```
/api/chat/
```

Body:

```json
{
  "conversation_id": 1,
  "message": "Explain Django authentication"
}
```

---

## 🔹 Get Conversation Messages

GET

```
/api/conversations/<id>/messages/
```

---

## 🔹 Rename Conversation

PATCH

```
/api/conversations/<id>/rename/
```

---

## 🔹 Delete Conversation

DELETE

```
/api/conversations/<id>/delete/
```

---

## 🔹 Regenerate AI Response

POST

```
/api/chat/regenerate/
```

---

# 🧠 How It Works

1. User sends message
2. Message saved to database
3. Last 20 messages sent to Gemini
4. Gemini generates response
5. AI response saved
6. If first user message → AI generates short conversation title

---

# 🗄️ Database Models

### Conversation

* id
* user (ForeignKey)
* title
* created_at

### ChatMessage

* conversation (ForeignKey)
* role (user / model)
* content
* timestamp

---

# 🔐 Security

* Token authentication required
* Conversations are user-specific
* Users cannot access others' chats

---

# 🧪 Testing

Test with:

* Postman
* Thunder Client
* curl

Make sure:

* Use trailing slash `/`
* Include Authorization header

---

# 📈 Future Improvements

* Pagination for messages
* Streaming AI responses
* Message editing
* Conversation folders
* WebSocket real-time chat
* Frontend (React / Next.js)
* Docker deployment
* PostgreSQL production setup
* Rate limiting
* AI model selector

---

# 🎯 Project Goal

This project demonstrates:

* REST API design
* Authentication system
* Database modeling
* AI integration
* Clean backend architecture
* ChatGPT-style conversation logic

---

# 👨‍💻 Author

Developed as a ChatGPT-style backend learning project using Django + Gemini AI.

---

3. Configure environment variables. You can set `GEMINI_API_KEY` in your shell or copy `.env.example` to `.env` and edit it.

```powershell
copy .env.example .env
# then edit .env to add your key
```

4. Run migrations and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

5. Open http://127.0.0.1:8000/ in your browser.

Notes

- The `chatbot/gemini.py` module will return a helpful placeholder string if the `google.generativeai` package or `GEMINI_API_KEY` is not available, so the app can run without that dependency.
- If you'd like a single-click start on Windows, use `runserver.bat`.
