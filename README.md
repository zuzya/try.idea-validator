# 🦄 AI Unicorn Validator

Валидация стартап-идей через синтетические интервью с AI-агентами.

## Требования

- Python 3.11+
- Node.js 18+
- API ключи: Google Gemini, OpenAI (в `.env`)

## Установка

### 1. Backend (Python)

```bash
# Создать виртуальное окружение (если не существует)
python -m venv .venv

# Активировать
source .venv/bin/activate  # macOS/Linux
# или
.venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt
# плюс FastAPI
pip install fastapi uvicorn
```

### 2. Frontend (Node.js)

```bash
cd frontend
npm install
```

## Запуск

### Терминал 1: Backend

```bash
# В корне проекта
.venv/bin/python -m uvicorn api:app --reload --port 8000
```

### Терминал 2: Frontend

```bash
cd frontend
npm run dev
```

## Использование

Открой в браузере: **http://localhost:5173**

1. Введи свою идею стартапа
2. Настрой параметры в боковой панели (опционально)
3. Нажми **"Start Validation"**
4. Наблюдай за процессом в реальном времени

## Архитектура

```
Backend (FastAPI)  ←→  Frontend (Vite + React)
      ↓                        ↑
  LangGraph Workflow      SSE Stream
```

- **Backend:** FastAPI с SSE для стриминга событий от LangGraph
- **Frontend:** React + Zustand для state management
- **Дизайн:** Темная тема с glassmorphism эффектами

## Основные файлы

- `api.py` — FastAPI сервер
- `main.py` — LangGraph workflow
- `frontend/src/App.jsx` — главный UI компонент
- `frontend/src/store/useValidationStore.js` — state management

## Примечания

- **Mock Mode** ускоряет тестирование (без реальных AI вызовов)
- **Debug Mode** использует быстрые модели (Gemini Flash)
- Старый Streamlit app (`app.py`) сохранён для совместимости
