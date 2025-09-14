# Anki Card Generator (apkg-maker)

Веб-сервис для создания файлов Anki (.apkg) через REST API. Позволяет генерировать колоды карточек с поддержкой HTML-контента и аудио.

## Возможности

- 📝 Создание карточек с HTML-контентом
- 🎵 Поддержка аудио (URL или base64)
- 📦 Генерация .apkg файлов для импорта в Anki
- 🚀 Fast API с автоматической документацией
- 🐳 Docker контейнеризация

## Быстрый старт

### Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn app:app --host 0.0.0.0 --port 8080
```

### Docker

```bash
# Сборка и запуск
docker-compose up -d

# Или через Docker
docker build -t apkg-maker .
docker run -p 8080:8080 apkg-maker
```

## API

### POST `/apkg`

Создает .apkg файл из переданных карточек.

**Параметры:**
```json
{
  "deckName": "English::Telegram",
  "notes": [
    {
      "front": "Hello",
      "backHtml": "<b>Привет</b>",
      "audioUrl": "https://example.com/audio.mp3",
      "audioBase64": "base64_encoded_audio"
    }
  ]
}
```

**Ответ:** .apkg файл для скачивания

### GET `/health`

Проверка работоспособности сервиса.

## Примеры использования

### cURL

```bash
curl -X POST "http://localhost:8080/apkg" \
  -H "Content-Type: application/json" \
  -d '{
    "deckName": "My Deck",
    "notes": [
      {
        "front": "Cat",
        "backHtml": "<b>Кот</b><br><i>домашнее животное</i>"
      }
    ]
  }' \
  --output my_deck.apkg
```

### Python

```python
import requests

data = {
    "deckName": "English Words",
    "notes": [
        {
            "front": "Dog",
            "backHtml": "<b>Собака</b>"
        }
    ]
}

response = requests.post("http://localhost:8080/apkg", json=data)
with open("deck.apkg", "wb") as f:
    f.write(response.content)
```

## Технологии

- **FastAPI** - веб-фреймворк
- **genanki** - библиотека для работы с Anki
- **httpx** - HTTP клиент для загрузки аудио
- **Python 3.11**

## Структура проекта

```
.
├── app.py              # Основной код приложения
├── requirements.txt    # Python зависимости
├── Dockerfile         # Docker образ
├── docker-compose.yml # Docker Compose конфигурация
└── README.md          # Документация
```

## Документация API

После запуска сервиса документация доступна по адресам:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`