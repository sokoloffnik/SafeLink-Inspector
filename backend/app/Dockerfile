# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY app/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY app/ .

# Указываем порт, который будет слушать приложение
EXPOSE 8000

# Запуск uvicorn сервера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]