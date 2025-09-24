import json
import uuid
import random
import asyncio
from datetime import datetime, date
from typing import Dict, List
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    AnalysisStatus,
)

# Дополнительная модель для preview с прогрессом
class PreviewResponse(BaseModel):
    processed: int
    total: int
    results: List[ResumeDetailResponse]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    load_demo_resumes()
    load_demo_vacancies()
    yield
    # Shutdown (if needed)

# Инициализация FastAPI приложения
app = FastAPI(
    title="WolfEye Mock Backend",
    description="Мок-бэкенд для анализа резюме",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
# Хранилище данных в памяти
transactions: Dict[str, Transaction] = {}
resumes: Dict[str, Resume] = {}
transaction_resume_links: List[TransactionResumeLink] = []
# Связь транзакций с вакансиями: {vacancy_id: [transaction_id1, transaction_id2, ...]}
vacancy_transactions: Dict[str, List[str]] = {}

# Демо-данные вакансий (загружаются из JSON файлов)
DEMO_VACANCIES = []

# Демо-данные резюме (загружаем из sample_resumes)
DEMO_RESUMES = [
    {
        "id": "3c07ff2f000f4e880700bb41f0435345554a79",
        "url": "https://hh.ru/resume/3c07ff2f000f4e880700bb41f0435345554a79",
        "data": {}
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
    },
    {
        "id": "22f2b4ee000f56dc5b00bb41f0564e71743246",
        "url": "https://hh.ru/resume/22f2b4ee000f56dc5b00bb41f0564e71743246",
        "data": {}
    },
    {
        "id": "37cd74c9000f1a765200bb41f0323133427552",
        "url": "https://hh.ru/resume/37cd74c9000f1a765200bb41f0323133427552",
        "data": {}
    },
    {
        "id": "108b9793000f5a420900bb41f052543668456f",
        "url": "https://hh.ru/resume/108b9793000f5a420900bb41f052543668456f",
        "data": {}
    },
    {
        "id": "201217d6000f50c6c300bb41f0474747393845",
        "url": "https://hh.ru/resume/201217d6000f50c6c300bb41f0474747393845",
        "data": {}
    }  
]

def load_demo_resumes():
    """Загружает демо-данные резюме из JSON файлов"""
    global DEMO_RESUMES
    
    resume_files = [
        "3c07ff2f000f4e880700bb41f0435345554a79.json",
        "13db2fbf000df537aa00bb41f05063456f6a39.json",
        "18c8bdbe000f4ab1d300bb41f0634b4a386c33.json",
        "22f2b4ee000f56dc5b00bb41f0564e71743246.json",
        "37cd74c9000f1a765200bb41f0323133427552.json",
        "108b9793000f5a420900bb41f052543668456f.json",
        "201217d6000f50c6c300bb41f0474747393845.json"
    ]
    
    for i, filename in enumerate(resume_files):
        try:
            file_path = f"../sample_resumes/{filename}"
            print(f"Loading {filename}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print(f"Warning: File {filename} is empty, using empty data")
                    DEMO_RESUMES[i]["data"] = {}
                    continue
                
                data = json.loads(content)
                DEMO_RESUMES[i]["data"] = data
                print(f"Successfully loaded {filename}")
                
        except FileNotFoundError:
            print(f"Warning: File {filename} not found, using empty data")
            DEMO_RESUMES[i]["data"] = {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filename}: {e}")
            print(f"File content preview: {content[:100]}...")
            DEMO_RESUMES[i]["data"] = {}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            DEMO_RESUMES[i]["data"] = {}

def load_demo_vacancies():
    """Загружает демо-данные вакансий из JSON файлов"""
    global DEMO_VACANCIES
    
    vacancy_files = ["1.json", "2.json", "3.json"]
    
    for filename in vacancy_files:
        try:
            file_path = f"../vacancies/{filename}"
            print(f"Loading vacancy {filename}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print(f"Warning: File {filename} is empty, skipping vacancy")
                    continue
                
                data = json.loads(content)
                DEMO_VACANCIES.append(data)
                print(f"Successfully loaded vacancy {filename}")
                
        except FileNotFoundError:
            print(f"Warning: File {filename} not found, skipping vacancy")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filename}: {e}")
            print(f"File content preview: {content[:100]}...")
        except Exception as e:
            print(f"Error loading {filename}: {e}")

def create_copy_legend(original_legend: Legend, resume_data: dict) -> Legend:
    """Создает копию легенды с небольшими изменениями для имитации копирования"""
    # Получаем данные из других резюме для создания "копии"
    other_resumes = [r for r in DEMO_RESUMES if r["id"] != resume_data.get("id", "")]
    
    if other_resumes:
        # Берем случайное резюме для "копирования"
        random_resume = random.choice(other_resumes)
        if random_resume["data"] and "experience" in random_resume["data"]:
            other_experience = random_resume["data"]["experience"]
            if other_experience:
                other_exp = random.choice(other_experience)
                other_company = other_exp.get("company", original_legend.company_name)
                other_position = other_exp.get("position", "Разработчик")
                
                # Создаем "копию" с данными из другого резюме
                copy_legend = Legend(
                    company_name=other_company,
                    start_date=original_legend.start_date,
                    end_date=original_legend.end_date,
                    legend_text=f"{other_position} в {other_company}"
                )
                return copy_legend
    
    # Если нет других резюме, создаем простую копию
    return Legend(
        company_name=original_legend.company_name,
        start_date=original_legend.start_date,
        end_date=original_legend.end_date,
        legend_text=original_legend.legend_text
    )

def extract_resume_id_from_url(url: str) -> str:
    """Извлекает ID резюме из URL"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'resume':
        return path_parts[1]
    return str(uuid.uuid4())

async def process_resumes_background(transaction_id: str, urls: List[str]):
    """Фоновая обработка резюме"""
    print(f"🚀 Начинаем фоновую обработку транзакции {transaction_id}")
    print(f"📋 URL для обработки: {urls}")
    
    try:
        # Создаем резюме и связи
        new_links = []
        
        for url in urls:
            resume_id = extract_resume_id_from_url(str(url))
            print(f"  🔍 Обрабатываем URL: {url} -> ID: {resume_id}")
            
            # Проверяем, есть ли уже такое резюме (переиспользование)
            if resume_id not in resumes:
                print(f"  📝 Создаем новое резюме {resume_id}")
                # Ищем в демо-данных
                demo_resume = next((r for r in DEMO_RESUMES if r["id"] == resume_id), None)
                if demo_resume:
                    print(f"  ✅ Найдено в демо-данных: {demo_resume['id']}")
                    resume_data = Resume(
                        id=resume_id,
                        url=str(url),
                        data=demo_resume["data"],
                        status="pending"
                    )
                else:
                    print(f"  ⚠️ Не найдено в демо-данных, создаем базовое")
                    # Создаем новое резюме
                    resume_data = Resume(
                        id=resume_id,
                        url=str(url),
                        status="pending"
                    )
                resumes[resume_id] = resume_data
                print(f"  📊 Статус резюме: {resume_data.status}")
            else:
                print(f"  ♻️ Резюме {resume_id} уже существует")
            
            # Создаем связь транзакция-резюме
            link = TransactionResumeLink(
                transaction_id=transaction_id,
                resume_id=resume_id
            )
            transaction_resume_links.append(link)
            new_links.append(link)
        
        # Обрабатываем резюме с задержкой
        print(f"🔄 Начинаем обработку {len(new_links)} резюме...")
        for i, link in enumerate(new_links):
            resume_id = link.resume_id
            if resume_id in resumes:
                resume = resumes[resume_id]
                print(f"⏳ Обрабатываем резюме {i+1}/{len(new_links)}: {resume_id}")
                print(f"  📊 Текущий статус: {resume.status}")
                
                # Эмуляция обработки - 3 секунды на каждое резюме
                print(f"  ⏰ Ждем 3 секунды...")
                await asyncio.sleep(3)
                
                if resume.data:
                    try:
                        processed_data = process_resume_data(resume.data)
                        resume.processed_data = processed_data
                        resume.status = "completed"
                        print(f"✅ Резюме {resume_id} обработано успешно")
                    except Exception as e:
                        resume.status = "failed"
                        print(f"❌ Ошибка обработки резюме {resume_id}: {e}")
                        # Создаем базовые данные для failed резюме
                        try:
                            processed_data = ResumeDetailResponse(
                                resume_id=resume_id,
                                score=30,  # Низкий рейтинг для failed резюме
                                fl_name="Error",
                                experience_months=0,
                                flags=[AnalysisFlag(name="Ошибка обработки", fact=str(e))],
                                years_old=25,
                                salary=0,
                                legends=[]
                            )
                            resume.processed_data = processed_data
                            resume.status = "completed"  # Меняем на completed чтобы транзакция завершилась
                            print(f"✅ Созданы базовые данные для failed резюме {resume_id}")
                        except Exception as e2:
                            print(f"❌ Критическая ошибка создания базовых данных: {e2}")
                else:
                    # Для резюме без данных создаем базовую информацию
                    try:
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
                        resume.status = "completed"
                        print(f"✅ Резюме {resume_id} обработано (базовые данные)")
                    except Exception as e:
                        resume.status = "failed"
                        print(f"❌ Ошибка создания базовых данных для {resume_id}: {e}")
        
        # Проверяем статус транзакции (завершена ли)
        linked_resume_ids = [link.resume_id for link in new_links]
        print(f"🔍 Проверяем статус транзакции {transaction_id}")
        print(f"  📋 Связанные резюме: {linked_resume_ids}")
        
        for resume_id in linked_resume_ids:
            if resume_id in resumes:
                resume = resumes[resume_id]
                print(f"  📄 Резюме {resume_id}: {resume.status}")
        
        all_completed = all(
            resumes[resume_id].status == "completed" 
            for resume_id in linked_resume_ids 
            if resume_id in resumes
        )
        print(f"  ✅ Все резюме завершены: {all_completed}")
        
        if all_completed and linked_resume_ids:
            transactions[transaction_id].status = "completed"
            transactions[transaction_id].completed_at = datetime.now()
            print(f"🎉 Транзакция {transaction_id} завершена!")
            print(f"📊 Статус обновлен: {transactions[transaction_id].status}")
            print(f"📅 Время завершения: {transactions[transaction_id].completed_at}")
        else:
            print(f"⚠️ Транзакция {transaction_id} не завершена полностью")
            print(f"📊 Текущий статус: {transactions[transaction_id].status}")
            
    except Exception as e:
        print(f"❌ Критическая ошибка в фоновой обработке {transaction_id}: {e}")
        if transaction_id in transactions:
            transactions[transaction_id].status = "failed"

# Функции анализа маркеров удалены - теперь используется мок-система



def get_mock_score_and_flags(resume_id: str) -> tuple[int, list[AnalysisFlag]]:
    """Возвращает мок-данные для конкретного резюме"""
    
    # Предопределенные мок-данные для каждого резюме
    mock_data = {
        "13db2fbf000df537aa00bb41f05063456f6a39": {  # Олег Устинов
            "score": 85,
            "flags": [
                AnalysisFlag(
                    name="Резюме выглядит достоверно", 
                    fact="Не обнаружено явных признаков накрутки. Все маркеры в норме."
                )
            ]
        },
        "108b9793000f5a420900bb41f052543668456f": {  # Илья Воробьев
            "score": 45,
            "flags": [
                AnalysisFlag(
                    name="Подозрительный опыт для возраста", 
                    fact="Возраст 23 года, но опыт 61 месяц. Возможно, накрутка опыта."
                ),
                AnalysisFlag(
                    name="Проблемы с образованием", 
                    fact="Неоконченное высшее образование при большом опыте работы."
                )
            ]
        },
        "18c8bdbe000f4ab1d300bb41f0634b4a386c33": {  # Антон Назаров
            "score": 72,
            "flags": [
                AnalysisFlag(
                    name="Проблемы с компаниями", 
                    fact="Отсутствуют ссылки на компании в опыте работы."
                )
            ]
        },
        "201217d6000f50c6c300bb41f0474747393845": {  # Кирилл Дагданча
            "score": 65,
            "flags": [
                AnalysisFlag(
                    name="Проблемы с компаниями", 
                    fact="Отсутствуют ссылки на компании в опыте работы."
                )
            ]
        },
        "22f2b4ee000f56dc5b00bb41f0564e71743246": {  # Александр Панарин
            "score": 55,
            "flags": [
                AnalysisFlag(
                    name="Проблемы с компаниями", 
                    fact="Отсутствуют ссылки на компании в опыте работы."
                )
            ]
        },
        "37cd74c9000f1a765200bb41f0323133427552": {  # Дмитрий Молочников
            "score": 55,
            "flags": [
                AnalysisFlag(
                    name="Проблемы с компаниями", 
                    fact="Отсутствуют ссылки на компании в опыте работы."
                )
            ]
        },
        "3c07ff2f000f4e880700bb41f0435345554a79": {  # Новиков Артем
            "score": 55,
            "flags": [
                AnalysisFlag(
                    name="Проблемы с компаниями", 
                    fact="Отсутствуют ссылки на компании в опыте работы."
                )
            ]
        }
    }
    
    # Возвращаем данные для конкретного резюме или дефолтные
    data = mock_data.get(resume_id, {
        "score": 50,
        "flags": [
            AnalysisFlag(
                name="Неизвестное резюме", 
                fact="Резюме не найдено в мок-данных."
            )
        ]
    })
    
    return data["score"], data["flags"]

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
    if age is None:
        age = 25  # Дефолтный возраст если не указан
    
    # Зарплата
    salary = resume_data.get("salary", 0)
    if salary is None:
        salary = 0  # Дефолтная зарплата если не указана
    
    # Получаем мок-данные для конкретного резюме
    score, flags = get_mock_score_and_flags(resume_id)
    
    # Создаем легенды (места работы)
    legends = []
    experience = resume_data.get("experience", [])
    for i, exp in enumerate(experience[:2]):  # Берем первые 2 места работы
        company = exp.get("company", "Неизвестная компания")
        position = exp.get("position", "Разработчик")
        start_date = exp.get("start", "")
        end_date = exp.get("end", "")
        
        # Создаем более детальное описание на основе данных из JSON
        description = exp.get("description", "")
        if description:
            # Берем первые 100 символов описания для legend_text
            short_desc = description[:100] + "..." if len(description) > 100 else description
            legend_text = f"{position} в {company}. {short_desc}"
        else:
            legend_text = f"{position} в {company}"
        
        original_legend = Legend(
            company_name=company,
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            legend_text=legend_text
        )
        
        # Каждая вторая легенда дублирует original_legend с similarity 80-100
        if i % 2 == 1:  # Вторая легенда (индекс 1)
            # Создаем "копию" с небольшими изменениями для имитации копирования
            copy_legend = create_copy_legend(original_legend, resume_data)
            similarity = random.randint(80, 100)
            legends.append(Legends(original_legend=original_legend, copy_legend=copy_legend, similarity=similarity))
        else:  # Первая легенда (индекс 0)
            legends.append(Legends(original_legend=original_legend, similarity=95))
    
    # Рейтинг уже получен из мок-данных выше
    
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
        vacancy_id = vacancy["id"]
        
        # Получаем последнюю транзакцию для этой вакансии
        vacancy_transaction_ids = vacancy_transactions.get(vacancy_id, [])
        last_transaction_id = ""
        
        if vacancy_transaction_ids:
            # Находим последнюю транзакцию по времени создания
            latest_transaction = None
            for transaction_id in vacancy_transaction_ids:
                if transaction_id in transactions:
                    transaction = transactions[transaction_id]
                    if latest_transaction is None or transaction.created_at > latest_transaction.created_at:
                        latest_transaction = transaction
            
            if latest_transaction:
                last_transaction_id = latest_transaction.id
        
        result.append(GetVacanciesResponse(
            name=vacancy["title"],
            transaction_id=last_transaction_id,  # ID последней транзакции
            count_respondents=vacancy["count_respondents"]
        ))
    return result

@app.post("/process_resumes", response_model=ProcessResumesResponse)
async def process_resumes(request: ProcessResumesRequest, background_tasks: BackgroundTasks):
    """Обработать список резюме (асинхронно)"""
    transaction_id = str(uuid.uuid4())
    
    try:
        # 1. Создаем транзакцию
        transaction = Transaction(
            id=transaction_id,
            name=request.name,
            status="processing",
            created_at=datetime.now()
        )
        transactions[transaction_id] = transaction
        
        # Привязываем транзакцию к случайной вакансии (для демо)
        if DEMO_VACANCIES:
            random_vacancy = random.choice(DEMO_VACANCIES)
            vacancy_id = random_vacancy["id"]
            if vacancy_id not in vacancy_transactions:
                vacancy_transactions[vacancy_id] = []
            vacancy_transactions[vacancy_id].append(transaction_id)
        
        # 2. Добавляем фоновую задачу для обработки резюме
        print(f"🚀 Добавляем фоновую задачу для транзакции {transaction_id}")
        background_tasks.add_task(process_resumes_background, transaction_id, request.urls)
        
        print(f"✅ Транзакция {transaction_id} создана, обработка запущена в фоне")
        return ProcessResumesResponse(transaction_id=transaction_id)
        
    except Exception as e:
        # В случае ошибки откатываем изменения
        if transaction_id in transactions:
            del transactions[transaction_id]
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {str(e)}")

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
    
    # Статус транзакции обновляется только в фоновой функции
    # Здесь мы только читаем текущий статус
    
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
    print(f"🔍 Получение всех транзакций. Всего: {len(transactions)}")
    
    for transaction in transactions.values():
        print(f"  📋 Транзакция {transaction.id}: {transaction.status} (завершена: {transaction.completed_at})")
        results.append(AnalysisTransactionStatus(
            transaction_id=transaction.id,
            name=transaction.name,
            status=transaction.status,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at
        ))
    
    return AllAnalysisResultsResponse(results=results)

@app.get("/preview/{transaction_id}", response_model=PreviewResponse)
async def get_preview(transaction_id: str):
    """Получить только обработанные резюме для транзакции с прогрессом"""
    if transaction_id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Находим все резюме для этой транзакции
    linked_resume_ids = [
        link.resume_id for link in transaction_resume_links 
        if link.transaction_id == transaction_id
    ]
    
    # Подсчитываем обработанные резюме
    processed_count = 0
    results = []
    
    print(f"🔍 Preview для транзакции {transaction_id}")
    print(f"  📋 Связанные резюме: {linked_resume_ids}")
    
    for resume_id in linked_resume_ids:
        if resume_id in resumes:
            resume = resumes[resume_id]
            print(f"  📄 Резюме {resume_id}: статус={resume.status}, processed_data={'есть' if resume.processed_data else 'нет'}")
            if resume.status == "completed" and resume.processed_data:
                processed_count += 1
                results.append(resume.processed_data)
    
    return PreviewResponse(
        processed=processed_count,
        total=len(linked_resume_ids),
        results=results
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
