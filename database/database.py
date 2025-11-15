# Функция для инициализации "базы данных"
def init_db():
    return {
        "user": {"partner": None, "game_files": []},
        "users": {},
        "congratulations": [],
    }