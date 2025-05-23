# Foodgram

## Развертывание

### Запуск проекта - backend

1. Клонирование репозитория и переход в директорию проекта

``` bash
    git clone https://github.com/Daniil141980/foodgram-st.git
    cd foodgram-st/backend
```

2. Создание и активация виртуального окружения

``` bash
    python -m venv venv
    venv\Scripts\activate
```

3. Установка зависимостей

``` bash
    python.exe -m pip install --upgrade pip 
    pip install -r requirements.txt
```

4. Применение миграций

``` bash
    python manage.py makemigrations
    python manage.py migrate
    python manage.py load_ingredients
```

6. Сбор статических файлов

``` bash
    python manage.py collectstatic --noinput
```

7. Запуск проекта

``` bash
    python manage.py runserver
```

* Сайт: http://127.0.0.1:8000
* Админ: http://127.0.0.1:8000/admin

### Развертывание с Docker

1. Установите Docker и Docker Compose

2. Запустите контейнеры:

``` bash
cd infra
docker-compose up -d
```

Три контейнера:

- frontend - фронтенд
- backend - API сервер
- nginx - веб-сервер