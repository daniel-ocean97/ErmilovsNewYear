from celery_test import send_test_message, test_pair

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК ТЕСТОВЫХ ЗАДАЧ CELERY")
    print("=" * 50)
    print("\n⚠️  ВАЖНО: Убедитесь, что Celery worker запущен!")
    print("   Запустите в отдельном терминале: celery -A celery_app worker -l info")
    print("   Или: python run_celery_worker.py\n")
    
    import time
    
    # Вариант 1: Запустить задачу асинхронно
    print("1. Запуск простой задачи...")
    try:
        result = send_test_message.delay()
        print(f"   ✅ Задача отправлена! ID: {result.id}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print("   Убедитесь, что Redis запущен и worker работает!")
        exit(1)
    
    # Вариант 2: Запустить и дождаться результата
    print("\n2. Запуск теста пары...")
    try:
        result2 = test_pair.apply_async()
        print(f"   ✅ Задача отправлена! ID: {result2.id}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print("   Убедитесь, что Redis запущен и worker работает!")
        exit(1)
    
    print("\n" + "=" * 50)
    print("Ожидание выполнения задач (10 секунд)...")
    time.sleep(10)
    
    try:
        print("\nПолучение результатов...")
        result1_value = result.get(timeout=5)
        print(f"✅ Результат задачи 1: {result1_value}")
        
        result2_value = result2.get(timeout=5)
        print(f"✅ Результат задачи 2: {result2_value}")
        
        print("\n" + "=" * 50)
        print("✅ Все тесты выполнены!")
    except Exception as e:
        print(f"\n❌ Не удалось получить результат: {e}")
        print("\nВозможные причины:")
        print("1. Celery worker не запущен")
        print("2. Redis не запущен")
        print("3. Задачи еще выполняются (попробуйте подождать дольше)")
        print("\nПроверьте логи worker для деталей!")