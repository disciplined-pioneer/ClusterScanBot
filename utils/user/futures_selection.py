import json
from pathlib import Path
from aiogram.fsm.state import State, StatesGroup

class FuturesStates(StatesGroup):
    futures_name = State()

def check_futures_presence(futures_name: str, json_path: str = "data/all_futures.json") -> str | None:
    """
    Проверяет, есть ли futures_name в JSON-массиве.

    :param futures_name: Имя фьючерса, введённое пользователем
    :param json_path: Путь к JSON-файлу с массивом фьючерсов
    :return: None, если фьючерс найден; иначе текст ошибки с введённым именем
    """
    futures_name_clean = futures_name.strip().upper()

    try:
        with open(Path(json_path), "r", encoding="utf-8") as f:
            all_futures = json.load(f)
    except Exception as e:
        # Если не удалось прочитать файл, возвращаем ошибку
        return futures_name_clean, f"Ошибка при чтении списка фьючерсов: {e}"

    if futures_name_clean not in all_futures:
        return futures_name_clean, f'❌ Фьючерс <i><b>"{futures_name}"</b></i> не найден. Попробуйте снова'

    return futures_name_clean, None
