#!/usr/bin/env python3
"""
Тест для проверки улучшений API:
1. Проверка загрузки вакансий из JSON
2. Проверка генерации copy_legend
3. Проверка количества откликов в вакансиях
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_vacancies():
    """Тест загрузки вакансий"""
    print("🔍 Тестируем загрузку вакансий...")
    
    try:
        response = requests.get(f"{BASE_URL}/vacancies")
        if response.status_code == 200:
            vacancies = response.json()
            print(f"✅ Загружено {len(vacancies)} вакансий")
            
            for vacancy in vacancies:
                print(f"  📋 {vacancy['name']} - {vacancy['count_respondents']} откликов")
            
            return True
        else:
            print(f"❌ Ошибка загрузки вакансий: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_resume_processing():
    """Тест обработки резюме с copy_legend"""
    print("\n🔍 Тестируем обработку резюме...")
    
    # URL резюме из sample_resumes
    resume_urls = [
        "https://hh.ru/resume/13db2fbf000df537aa00bb41f05063456f6a39",
        "https://hh.ru/resume/108b9793000f5a420900bb41f052543668456f"
    ]
    
    try:
        # Создаем транзакцию
        response = requests.post(f"{BASE_URL}/process_resumes", json={
            "name": "Тест улучшений API",
            "urls": resume_urls
        })
        
        if response.status_code == 200:
            data = response.json()
            transaction_id = data["transaction_id"]
            print(f"✅ Транзакция создана: {transaction_id}")
            
            # Проверяем preview с прогрессом
            print("🔍 Проверяем preview с прогрессом...")
            preview_response = requests.get(f"{BASE_URL}/preview/{transaction_id}")
            if preview_response.status_code == 200:
                preview = preview_response.json()
                print(f"  📊 Прогресс: {preview['processed']}/{preview['total']} резюме обработано")
            
            # Ждем обработки (каждое резюме обрабатывается 3 секунды)
            print("⏳ Ожидание обработки резюме (6 секунд)...")
            time.sleep(7)  # Немного больше чем 6 секунд для 2 резюме
            
            # Проверяем preview после обработки
            preview_response = requests.get(f"{BASE_URL}/preview/{transaction_id}")
            if preview_response.status_code == 200:
                preview = preview_response.json()
                print(f"  📊 Прогресс после обработки: {preview['processed']}/{preview['total']} резюме обработано")
            
            # Получаем результаты
            results_response = requests.get(f"{BASE_URL}/results/{transaction_id}")
            if results_response.status_code == 200:
                results = results_response.json()
                print(f"✅ Получены результаты для {len(results['results'])} резюме")
                print(f"  📊 Статус транзакции: {results['status']}")
                
                # Проверяем copy_legend
                for result in results["results"]:
                    print(f"\n📄 Резюме: {result['fl_name']}")
                    print(f"  🏢 Легенды:")
                    
                    for i, legend in enumerate(result["legends"]):
                        print(f"    {i+1}. Оригинал: {legend['original_legend']['company_name']}")
                        if legend.get("copy_legend"):
                            print(f"       Копия: {legend['copy_legend']['company_name']} (similarity: {legend['similarity']}%)")
                        else:
                            print(f"       Копия: отсутствует")
                
                return True
            else:
                print(f"❌ Ошибка получения результатов: {results_response.status_code}")
                return False
        else:
            print(f"❌ Ошибка создания транзакции: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка обработки резюме: {e}")
        return False

def test_vacancy_transactions():
    """Тест связи транзакций с вакансиями"""
    print("\n🔍 Тестируем связь транзакций с вакансиями...")
    
    try:
        # Получаем вакансии
        response = requests.get(f"{BASE_URL}/vacancies")
        if response.status_code == 200:
            vacancies = response.json()
            print(f"✅ Загружено {len(vacancies)} вакансий")
            
            for vacancy in vacancies:
                print(f"  📋 {vacancy['name']}")
                print(f"     👥 Откликов: {vacancy['count_respondents']}")
                print(f"     🔄 Транзакций: {len(vacancy['all_transactions'])}")
                
                for transaction in vacancy['all_transactions']:
                    print(f"       - {transaction['name']} ({transaction['status']})")
            
            return True
        else:
            print(f"❌ Ошибка загрузки вакансий: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка тестирования вакансий: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов улучшений API...")
    
    # Ждем запуска сервера
    print("⏳ Ожидание запуска сервера...")
    time.sleep(3)
    
    # Тестируем вакансии
    vacancies_ok = test_vacancies()
    
    # Тестируем связь транзакций с вакансиями
    transactions_ok = test_vacancy_transactions()
    
    # Тестируем обработку резюме
    resumes_ok = test_resume_processing()
    
    # Итоги
    print("\n📊 Результаты тестирования:")
    print(f"  Вакансии: {'✅' if vacancies_ok else '❌'}")
    print(f"  Транзакции: {'✅' if transactions_ok else '❌'}")
    print(f"  Резюме: {'✅' if resumes_ok else '❌'}")
    
    if vacancies_ok and transactions_ok and resumes_ok:
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n⚠️ Некоторые тесты не прошли")

if __name__ == "__main__":
    main()
