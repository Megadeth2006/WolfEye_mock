import json
import uuid
from datetime import datetime
from typing import Dict, List
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from pydantic import HttpUrl

from analysis import (
    AnalysisTransactionStatus,
    GetResultsResponse,
    GetVacanciesResponse,
    ProcessResumesRequest,
    ProcessResumesResponse,
    Resume,
    ResumeDetailResponse,
    Transaction,
    TransactionResumeLink,
    AllAnalysisResultsResponse,
    AnalysisFlag,
    Legend,
    Legends,
    AnalysisStatus,
    Status,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    load_demo_resumes()
    yield
    # Shutdown (if needed)

# Инициализация FastAPI приложения
app = FastAPI(
    title="WolfEye Mock Backend",
    description="Мок-бэкенд для анализа резюме",
    version="1.0.0",
    lifespan=lifespan
)

# Хранилище данных в памяти
transactions: Dict[str, Transaction] = {}
resumes: Dict[str, Resume] = {}
transaction_resume_links: List[TransactionResumeLink] = []

# Демо-данные вакансий (простые словари)
DEMO_VACANCIES = [
    {
        "id": "vac_1",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "salary_from": 150000,
        "salary_to": 250000,
        "location": "Москва",
        "description": "Ищем опытного Python разработчика для работы над высоконагруженными системами"
    },
    {
        "id": "vac_2", 
        "title": "C# .NET Developer",
        "company": "BankSoft",
        "salary_from": 120000,
        "salary_to": 200000,
        "location": "Санкт-Петербург",
        "description": "Разработка финансовых приложений на .NET Core"
    },
    {
        "id": "vac_3",
        "title": "Full Stack Developer",
        "company": "StartupInc",
        "salary_from": 100000,
        "salary_to": 180000,
        "location": "Удаленно",
        "description": "Полный цикл разработки веб-приложений"
    }
]

# Демо-данные резюме (загружаем из sample_resumes)
DEMO_RESUMES = [
    {
        "id": "108b9793000f5a420900bb41f052543668456f",
        "url": "https://hh.ru/resume/108b9793000f5a420900bb41f052543668456f",
        "data": {}  # Будет загружено из JSON файла
    },
    {
        "id": "13db2fbf000df537aa00bb41f05063456f6a39", 
        "url": "https://hh.ru/resume/13db2fbf000df537aa00bb41f05063456f6a39",
        "data": {}
    },
    {
        "id": "18c8bdbe000f4ab1d300bb41f0634b4a386c33",
        "url": "https://hh.ru/resume/18c8bdbe000f4ab1d300bb41f0634b4a386c33", 
        "data": {}
    }
]

def load_demo_resumes():
    """Загружает демо-данные резюме из JSON файлов"""
    global DEMO_RESUMES
    
    resume_files = [
        "108b9793000f5a420900bb41f052543668456f.json",
        "13db2fbf000df537aa00bb41f05063456f6a39.json", 
        "18c8bdbe000f4ab1d300bb41f0634b4a386c33.json"
    ]
    
    for i, filename in enumerate(resume_files):
        try:
            with open(f"../sample_resumes/{filename}", "r", encoding="utf-8") as f:
                data = json.load(f)
                DEMO_RESUMES[i]["data"] = data
        except FileNotFoundError:
            print(f"Warning: File {filename} not found, using empty data")

def extract_resume_id_from_url(url: str) -> str:
    """Извлекает ID резюме из URL"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'resume':
        return path_parts[1]
    return str(uuid.uuid4())

def process_resume_data(resume_data: dict) -> ResumeDetailResponse:
    """Обрабатывает данные резюме и создает ResumeDetailResponse"""
    # Извлекаем основные данные
    resume_id = resume_data.get("id", "")
    first_name = resume_data.get("first_name", "")
    last_name = resume_data.get("last_name", "")
    fl_name = f"{first_name[0]}. {last_name}" if first_name and last_name else "Unknown"
    
    # Опыт работы в месяцах
    total_experience = resume_data.get("total_experience", {})
    experience_months = total_experience.get("months", 0) if total_experience else 0
    
    # Возраст
    age = resume_data.get("age", 25)
    
    # Зарплата
    salary = resume_data.get("salary", 0) or 100000  # Дефолтная зарплата
    
    # Создаем флаги анализа (демо)
    flags = [
        AnalysisFlag(name="Опыт работы", fact=f"Опыт: {experience_months} месяцев"),
        AnalysisFlag(name="Образование", fact="Высшее техническое образование")
    ]
    
    # Создаем легенды (места работы)
    legends = []
    experience = resume_data.get("experience", [])
    for exp in experience[:2]:  # Берем первые 2 места работы
        company = exp.get("company", "Неизвестная компания")
        position = exp.get("position", "Разработчик")
        start_date = exp.get("start", "")
        end_date = exp.get("end", "")
        
        legend = Legend(
            company_name=company,
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            legend_text=f"{position} в {company}"
        )
        
        legends.append(Legends(original_legend=legend, similarity=95))
    
    # Вычисляем общий рейтинг (демо-логика)
    score = min(95, max(60, 70 + (experience_months // 12) * 2))
    
    return ResumeDetailResponse(
        resume_id=resume_id,
        score=score,
        fl_name=fl_name,
        experience_months=experience_months,
        flags=flags,
        years_old=age,
        salary=salary,
        legends=legends
    )


@app.get("/vacancies", response_model=List[GetVacanciesResponse])
async def get_vacancies():
    """Получить список вакансий"""
    result = []
    for vacancy in DEMO_VACANCIES:
        # Создаем транзакцию для каждой вакансии (демо)
        transaction_id = str(uuid.uuid4())
        result.append(GetVacanciesResponse(
            name=vacancy["title"],
            transaction_id=transaction_id,
            count_respondents=len([r for r in resumes.values() if r.status == Status.COMPLETED])
        ))
    return result

@app.post("/process_resumes", response_model=ProcessResumesResponse)
async def process_resumes(request: ProcessResumesRequest):
    """Обработать список резюме"""
    transaction_id = str(uuid.uuid4())
    
    # Создаем транзакцию
    transaction = Transaction(
        id=transaction_id,
        name=request.name,
        status=Status.PROCESSING,
        created_at=datetime.now()
    )
    transactions[transaction_id] = transaction
    
    # Обрабатываем каждое резюме
    for url in request.urls:
        resume_id = extract_resume_id_from_url(str(url))
        
        # Проверяем, есть ли уже такое резюме
        if resume_id not in resumes:
            # Ищем в демо-данных
            demo_resume = next((r for r in DEMO_RESUMES if r["id"] == resume_id), None)
            if demo_resume:
                resume_data = Resume(
                    id=resume_id,
                    url=str(url),
                    data=demo_resume["data"],
                    status=Status.PENDING
                )
            else:
                # Создаем новое резюме
                resume_data = Resume(
                    id=resume_id,
                    url=str(url),
                    status=Status.PENDING
                )
            resumes[resume_id] = resume_data
        
        # Создаем связь транзакция-резюме
        link = TransactionResumeLink(
            transaction_id=transaction_id,
            resume_id=resume_id
        )
        transaction_resume_links.append(link)
        
        # Обрабатываем резюме (демо-логика)
        if resume_id in resumes:
            resume = resumes[resume_id]
            if resume.data:
                try:
                    processed_data = process_resume_data(resume.data)
                    resume.processed_data = processed_data
                    resume.status = Status.COMPLETED
                except Exception as e:
                    resume.status = Status.FAILED
                    print(f"Error processing resume {resume_id}: {e}")
            else:
                # Для резюме без данных создаем базовую информацию
                try:
                    # Создаем минимальную обработанную информацию
                    processed_data = ResumeDetailResponse(
                        resume_id=resume_id,
                        score=50,  # Базовый рейтинг
                        fl_name="Unknown",
                        experience_months=0,
                        flags=[AnalysisFlag(name="Нет данных", fact="Резюме не найдено в демо-данных")],
                        years_old=25,
                        salary=50000,
                        legends=[]
                    )
                    resume.processed_data = processed_data
                    resume.status = Status.COMPLETED
                except Exception as e:
                    resume.status = Status.FAILED
                    print(f"Error creating basic resume data for {resume_id}: {e}")
    
    return ProcessResumesResponse(transaction_id=transaction_id)

@app.get("/results/{transaction_id}", response_model=GetResultsResponse)
async def get_results(transaction_id: str):
    """Получить результаты по транзакции"""
    if transaction_id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    transaction = transactions[transaction_id]
    
    # Находим все резюме для этой транзакции
    linked_resume_ids = [
        link.resume_id for link in transaction_resume_links 
        if link.transaction_id == transaction_id
    ]
    
    results = []
    for resume_id in linked_resume_ids:
        if resume_id in resumes:
            resume = resumes[resume_id]
            if resume.processed_data:
                results.append(resume.processed_data)
    
    # Определяем статус транзакции
    all_completed = all(
        resumes[resume_id].status == Status.COMPLETED 
        for resume_id in linked_resume_ids 
        if resume_id in resumes
    )
    
    if all_completed and linked_resume_ids:
        transaction.status = Status.COMPLETED
        transaction.completed_at = datetime.now()
    
    return GetResultsResponse(
        transaction_id=transaction_id,
        status=transaction.status,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
        results=results
    )

@app.get("/all_results", response_model=AllAnalysisResultsResponse)
async def get_all_results():
    """Получить список всех транзакций"""
    results = []
    for transaction in transactions.values():
        results.append(AnalysisTransactionStatus(
            transaction_id=transaction.id,
            name=transaction.name,
            status=transaction.status,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at
        ))
    
    return AllAnalysisResultsResponse(results=results)

@app.get("/preview/{transaction_id}", response_model=List[ResumeDetailResponse])
async def get_preview(transaction_id: str):
    """Получить только обработанные резюме для транзакции"""
    if transaction_id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Находим все резюме для этой транзакции
    linked_resume_ids = [
        link.resume_id for link in transaction_resume_links 
        if link.transaction_id == transaction_id
    ]
    
    results = []
    for resume_id in linked_resume_ids:
        if resume_id in resumes:
            resume = resumes[resume_id]
            if resume.status == Status.COMPLETED and resume.processed_data:
                results.append(resume.processed_data)
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
