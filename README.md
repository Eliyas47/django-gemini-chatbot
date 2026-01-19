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
