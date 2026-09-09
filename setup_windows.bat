@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
echo.
echo Setup complete.
echo Create an admin with: python manage.py createsuperuser
echo Then run: python manage.py runserver
pause
