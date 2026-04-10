# Базовый образ Python 3.9
FROM python:3.9-slim

# Устанавливаем компиляторы для C-библиотек (нужны для scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-библиотеки
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY ./app ./app

# Открываем порт для API
EXPOSE 8000

# Запускаем FastAPI сервер
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]