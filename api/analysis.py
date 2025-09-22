from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl

# ---------- Общие типы ----------
NonNegInt = Annotated[int, Field(ge=0)]
Percent = Annotated[int, Field(ge=0, le=100)]
AgeYears = Annotated[int, Field(ge=0, le=120)]

# ---------- Респонсы/запросы ----------

# Получить список вакансий (новый роут)
class GetVacanciesResponse(BaseModel):
    """Демка: список вакансий и предложений на них"""
    name: str = Field(..., description="Название вакансии")
    transaction_id: str = Field(..., description="ID новой транзакции для отслеживания результатов")
    count_respondents: NonNegInt = Field(..., description="Количество респондентов")
    all_transactions: list[Transaction] = Field(default_factory=list, description="Все транзакции для этой вакансии")


class ProcessResumesRequest(BaseModel):
    """Запрос на обработку списка резюме"""
    name: str = Field(..., description="Название транзакции")
    urls: list[HttpUrl] = Field(..., description="Список URL резюме с hh.ru")


class ProcessResumesResponse(BaseModel):
    """Ответ с ID транзакции"""
    transaction_id: str = Field(..., description="ID транзакции для отслеживания результатов")


class AnalysisFlag(BaseModel):
    """Флаги анализа для различных компонентов резюме"""
    name: str = Field(..., min_length=1, description="Название red-флага")
    fact: str = Field(..., min_length=1, description="Причина")


class Legend(BaseModel):
    company_name: str = Field(..., description="Название компании")
    start_date: date | None = Field(None, description="Дата начала")
    end_date: date | None = Field(None, description="Дата увольнения")
    legend_text: str | None = Field(None, description="Текст легенды")


class Legends(BaseModel):
    original_legend: Legend
    copy_legend: Legend | None = None
    similarity: Percent = 0  # 0..100


class ResumeDetailResponse(BaseModel):
    """Детальная информация о резюме"""
    resume_id: str = Field(..., description="ID резюме")
    score: Percent = Field(..., description="Общий рейтинг резюме (0-100)")
    fl_name: str = Field(..., description="Имя Ф. (только первая буква)")
    experience_months: NonNegInt | None = Field(None, description="Месяцы опыта")
    flags: list[AnalysisFlag] = Field(default_factory=list, description="RED-флаги анализа")
    years_old: AgeYears = Field(..., description="Полных лет (или оценка)")
    salary: NonNegInt = Field(..., description="Желаемая ЗП")
    legends: list[Legends] = Field(default_factory=list, description="Места работы + дубликаты")


# Общий набор статусов на уровне API
AnalysisStatus = Literal["pending", "processing", "completed", "failed"]

class GetResultsResponse(BaseModel):
    """Ответ со списком результатов анализа"""
    transaction_id: str = Field(..., description="ID транзакции")
    status: AnalysisStatus = Field(..., description="Статус обработки")
    created_at: datetime = Field(..., description="Время создания транзакции")
    completed_at: datetime | None = Field(None, description="Время завершения обработки")
    results: list[ResumeDetailResponse] = Field(default_factory=list, description="Список обработанных резюме")


class AnalysisTransactionStatus(BaseModel):
    """Краткая информация о транзакции анализа"""
    transaction_id: str = Field(..., description="ID транзакции")
    name: str = Field(..., description="Название транзакции")
    status: AnalysisStatus = Field(..., description="Статус обработки")
    created_at: datetime = Field(..., description="Время создания транзакции")
    completed_at: datetime | None = Field(None, description="Время завершения обработки")


class AllAnalysisResultsResponse(BaseModel):
    """Ответ со списком всех транзакций анализа"""
    results: list[AnalysisTransactionStatus] = Field(default_factory=list, description="Список всех транзакций анализа")


# ---------- Модели для внутреннего хранения данных ----------

class Transaction(BaseModel):
    """Модель транзакции для хранения в памяти"""
    id: str = Field(..., description="ID транзакции")
    name: str = Field(..., description="Название транзакции")
    status: AnalysisStatus = Field(..., description="Статус транзакции")
    created_at: datetime = Field(..., description="Время создания")
    completed_at: datetime | None = Field(None, description="Время завершения")


class Resume(BaseModel):
    """Модель резюме для хранения в памяти"""
    id: str = Field(..., description="ID резюме")
    status: AnalysisStatus = Field(default="pending", description="Статус обработки резюме")
    url: str = Field(..., description="URL резюме")
    data: dict = Field(default_factory=dict, description="Данные резюме из JSON")
    processed_data: ResumeDetailResponse | None = Field(None, description="Обработанные данные резюме")


class TransactionResumeLink(BaseModel):
    """Связь между транзакцией и резюме"""
    transaction_id: str = Field(..., description="ID транзакции")
    resume_id: str = Field(..., description="ID резюме")

