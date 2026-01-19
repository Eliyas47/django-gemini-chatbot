@echo off
if not exist "venv\Scripts\activate.bat" (
  echo Virtual environment not found. Create with: python -m venv venv
  exit /b 1
)
call venv\Scripts\activate.bat
python manage.py migrate
python manage.py runserver
