import json
import time
from pathlib import Path
from aiogram import types
from aiogram.fsm.state import State, StatesGroup

import services.futures_selection as a
import bot.templates.user.futures_selection as t

from core.logger import filter_futures_logger as logger

from integrations.binance.volume_profile import get_vap_levels
from integrations.binance.downloading_data import AsyncCryptoDataFetcher
from integrations.machine_learning.isolation_forest import AnomalyDetector


# Импортируем все классы
fetcher = AsyncCryptoDataFetcher()
visualizer = a.FuturesVisualizer()
detector = AnomalyDetector(contamination=0.1, scale_by='column')


class FuturesStates(StatesGroup):
    futures_name = State()

ALL_LIST_TIMEFRAMES = ['1d', '4h', '1h', '30m', '15m', '5m']


def sort_timeframes(timeframes: list[str]) -> list[str]:
    order = {tf: i for i, tf in enumerate(ALL_LIST_TIMEFRAMES)}
    return sorted(timeframes, key=lambda x: order.get(x, len(order)))


def split_timeframes(timeframes: list[str]) -> tuple[list[str], list[str]]:
    senior = [tf for tf in timeframes if tf in ("1d", "4h")]
    junior = [tf for tf in timeframes if tf not in ("1d", "4h")]
    return senior, junior


def normalize_symbol(symbol: str) -> str:
    """Приводит тикер фьючерса к формату BTCUSDT вне зависимости от ввода."""
    symbol = symbol.strip().upper()
    symbol = symbol.replace("/", "").replace("-", "")

    # если тикер уже оканчивается на USDT
    if symbol.endswith("USDT"):
        return symbol

    # если тикер заканчивается на USD — добавим T
    if symbol.endswith("USD"):
        return symbol + "T"

    # если указана только база, добавляем USDT
    return symbol + "USDT"


def check_futures_presence(futures_name: str, json_path: str = "data/all_futures.json") -> str | None:
    """
    Проверяет, есть ли futures_name в JSON-массиве.

    :param futures_name: Имя фьючерса, введённое пользователем
    :param json_path: Путь к JSON-файлу с массивом фьючерсов
    :return: None, если фьючерс найден; иначе текст ошибки с введённым именем
    """
    futures_name_clean = normalize_symbol(futures_name)

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
    start = time.time()
    await callback.message.edit_text(t.start_data_collection_msg)
    sorted_tfs = sort_timeframes(list_timeframes)
    senior_tfs, junior_tfs = split_timeframes(sorted_tfs)

    # Скачиваем данные с биржи Binance
    combined_data = {}
    if senior_tfs:
        senior_combined_data = await fetcher.download_price(
            futures_name, senior_tfs, limit=500, save=True
        )
        combined_data.update(senior_combined_data)

    if junior_tfs:
        junior_combined_data = await fetcher.download_info(
            futures_name, junior_tfs, limit=500, save=True
        )
        combined_data.update(junior_combined_data)

    logger.info('Данные были скачаны!')
    await callback.message.edit_text(t.data_collection_finished_msg)

    # Ищем аномалии в каждом из ТФ
    for n, tf in enumerate(sorted_tfs, start=1):
        df = combined_data.get((futures_name[0], tf))
        if df is None:
            logger.warning(f"[{tf}] Нет данных для анализа!")
            continue

        # Поиск аномалий и уровней
        result = detector.run(df, columns="volume", direction='up')
        vap_levels = get_vap_levels(df)

        # Создаём графики
        if tf in junior_tfs:
            visualizer.visualize_anomalies_junior(
                data=result,
                vap_levels=vap_levels,
                futures_name=futures_name[0],
                time_frame=tf,
                number=n
            )

        if tf in senior_tfs:
            visualizer.visualize_anomalies_senior(
                data=result,
                vap_levels=vap_levels,
                futures_name=futures_name[0],
                time_frame=tf,
                number=n
            )

    # Список всех путей к файлам
    end = time.time()
    files = visualizer.get_saved_files()
    logger.info(f"Сохранено файлов: {len(files)} - ({end-start:.2f} сек)")

    logger.info('Анализ фьючерса завершён!')
    await callback.message.edit_text(t.futures_analyzed_msg)
    
    visualizer.saved_files = []
    return files
