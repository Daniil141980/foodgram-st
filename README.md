### Запуск проекта для тестов

``` bash
    cd foodgram-st/backend
    python -m venv venv
    venv\Scripts\activate
    python.exe -m pip install --upgrade pip
    pip install -r requirements.txt
    python manage.py makemigrations
    python manage.py migrate
    python manage.py load_ingredients
    python manage.py runserver
```

Запускаем тесты в Postman. (Все работает)

### Docker

``` bash
cd infra
docker-compose up -d
```