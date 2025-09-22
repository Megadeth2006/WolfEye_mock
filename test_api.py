#!/usr/bin/env python3
"""
Простой тест для проверки API WolfEye Mock Backend
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_vacancies():
    """Тест получения вакансий"""
    print("Testing GET /vacancies...")
    try:
        response = requests.get(f"{BASE_URL}/vacancies")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_process_resumes():
    """Тест обработки резюме"""
    print("\nTesting POST /process_resumes...")
    try:
        data = {
            "name": "Тестовая транзакция",
            "urls": [
                "https://hh.ru/resume/108b9793000f5a420900bb41f052543668456f",
                "https://hh.ru/resume/13db2fbf000df537aa00bb41f05063456f6a39"
            ]
        }
        response = requests.post(f"{BASE_URL}/process_resumes", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            return response.json().get("transaction_id")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_results(transaction_id):
    """Тест получения результатов"""
    print(f"\nTesting GET /results/{transaction_id}...")
    try:
        response = requests.get(f"{BASE_URL}/results/{transaction_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_all_results():
    """Тест получения всех результатов"""
    print("\nTesting GET /all_results...")
    try:
        response = requests.get(f"{BASE_URL}/all_results")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_preview(transaction_id):
    """Тест получения превью"""
    print(f"\nTesting GET /preview/{transaction_id}...")
    try:
        response = requests.get(f"{BASE_URL}/preview/{transaction_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("WolfEye Mock Backend API Test")
    print("=" * 40)
    
    # Ждем немного, чтобы сервер запустился
    print("Waiting for server to start...")
    time.sleep(2)
    
    # Тестируем все endpoints
    tests = [
        ("Vacancies", test_vacancies),
        ("All Results", test_all_results),
    ]
    
    transaction_id = None
    
    # Тест обработки резюме
    transaction_id = test_process_resumes()
    if transaction_id:
        tests.extend([
            ("Get Results", lambda: test_get_results(transaction_id)),
            ("Preview", lambda: test_preview(transaction_id)),
        ])
    
    # Запускаем все тесты
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            print(f"✅ {test_name} - PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} - FAILED")
    
    print(f"\n{'='*40}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed!")

if __name__ == "__main__":
    main()
