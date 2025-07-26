# Используем официальный Python образ
FROM python:3.11-slim

# Обновление pip и установка зависимостей
RUN pip install --upgrade pip

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости и проект
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Запуск бота
CMD ["python", "run.py"]