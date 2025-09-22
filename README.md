# WolfEye Mock Backend

Минимальный мок-бэкенд на FastAPI для анализа резюме.

## Установка и запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите сервер:
```bash
cd api
python main.py
```

Или с помощью uvicorn:
```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. Откройте документацию API:
http://localhost:8000/docs

## API Endpoints

### GET /vacancies
Возвращает список вакансий с количеством респондентов.

### POST /process_resumes
Принимает список URL резюме и название транзакции. Создает транзакцию и обрабатывает резюме.

**Пример запроса:**
```json
{
  "name": "Анализ резюме для Python разработчика",
  "urls": [
    "https://hh.ru/resume/108b9793000f5a420900bb41f052543668456f",
    "https://hh.ru/resume/13db2fbf000df537aa00bb41f05063456f6a39"
  ]
}
```

### GET /results/{transaction_id}
Возвращает все резюме, связанные с транзакцией.

### GET /all_results
Возвращает список всех транзакций с краткой информацией.

### GET /preview/{transaction_id}
Возвращает только обработанные резюме для транзакции.

## Структура проекта

- `api/analysis.py` - Pydantic модели для API
- `api/main.py` - FastAPI приложение с роутами
- `requirements.txt` - Зависимости Python
- `sample_resumes/` - Примеры резюме в JSON формате

## Особенности

- Данные хранятся в памяти (dict/list)
- Демо-данные включают 3 вакансии и 3 резюме
- Статусы транзакций: "processing", "completed"
- Статусы резюме: "in_progress", "completed", "error"
- Автоматическая обработка резюме при создании транзакции
