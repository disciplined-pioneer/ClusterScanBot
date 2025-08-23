import json
from pathlib import Path
from aiogram import types
from aiogram.fsm.state import State, StatesGroup

import bot.templates.user.futures_selection as t
from core.logger import filter_futures_logger as logger

from integrations.binance.downloading_data import AsyncCryptoDataFetcher
from integrations.machine_learning.isolation_forest import AnomalyDetector


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


async def futures_analysis(callback: types.CallbackQuery, list_timeframes: list, futures_name: list):

    # Старт сбора данных
    await callback.message.edit_text(t.start_data_collection_msg)

    # Скачиваем данные с биржи Binance
    fetcher = AsyncCryptoDataFetcher(save_dir="data/klines")
    combined_data = await fetcher.download_price(futures_name, list_timeframes, limit=1500, save=True)

    logger.info('Данные были скачаны!')
    await callback.message.edit_text(t.data_collection_finished_msg)

    # Ищем аномалии в каждом из ТФ
    for tf in list_timeframes:
        df = combined_data.get((futures_name[0], tf))
        detector = AnomalyDetector(contamination=0.1, scale_by='column')
        result = detector.run(df, columns="volume", direction='up')
        file_path_csv = f"data/csv/{futures_name[0]}_{tf}_anomaly.csv"
        result.to_csv(file_path_csv)

    logger.info('Анализ фьючерса завершён!')
    await callback.message.edit_text(t.futures_analyzed_msg)