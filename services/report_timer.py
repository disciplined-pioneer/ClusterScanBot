import asyncio
from datetime import datetime, timedelta

from core.bot import bot
from settings import settings
from core.logger import filter_futures_logger as logger

from db.psql.models.models import Futures
import bot.templates.user.report_timer as t
from integrations.machine_learning.isolation_forest import AnomalyDetector
from integrations.binance.downloading_data import AsyncCryptoDataFetcher, volumes_table


class TaskScheduler:

    def __init__(self, interval_days: int = 3):
        """
        Планировщик задач.
        :param interval_days: Интервал в днях между запусками задачи.
        """
        self.interval_seconds = interval_days * 24 * 60 * 60
        self._stop_event = asyncio.Event()

    async def task(self):
        """Основной цикл работы"""
        logger.info("🛠 Скачиваем данные...")

        # Скачиваем данные с биржи Binance
        fetcher = AsyncCryptoDataFetcher(save_dir="data/klines")
        futures = fetcher.load_futures_from_json(path='data/all_futures.json')

        combined_data = await fetcher.download_price(futures, ["15m"], limit=288, save=True)
        logger.info('Данные были скачаны!')

        # Анализ с помощью изоляционного леса
        logger.info("Фильтруем фьючерсы...")
        df_vol = volumes_table(combined_data, tf="15m", bars=288)

        # scale_by='row' → стандартизация по строкам (по каждому фьючерсу)
        detector = AnomalyDetector(contamination=0.05, scale_by='row')
        result = detector.run(df_vol, columns="ALL", direction='up')
        result.to_csv("VOLUME.csv")

        # Изменяем в базе список фьючерсов
        new_list_futures = result[result['is_anomaly']].index.tolist()
        object_futures = await Futures.get(id=1)

        # Гарантируем, что old_list_futures всегда определён
        old_list_futures = object_futures.futures if object_futures else []

        if object_futures is None and new_list_futures:
            await Futures.create(futures=new_list_futures)
        elif new_list_futures:
            await object_futures.update(futures=new_list_futures)

        # Отправляем сообщения администраторам
        text = t.format_futures_update(old_list_futures, new_list_futures)
        for user_id in settings.bot.ADMINS:
            try:
                await bot.send_message(chat_id=user_id, text=text)
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение админу {user_id}: {e}")

        logger.info("✅ Задача выполнена, фьючерсы заменены!")

    async def run_once(self):
        """Выполнить задачу один раз с логированием."""
        start_time = datetime.now()
        logger.info(f"🚀 Запуск задачи: {start_time:%Y-%m-%d %H:%M:%S}")

        try:
            await self.task()
        except Exception as e:
            logger.exception(f"❌ Ошибка при выполнении задачи: {e}")

        next_run_time = datetime.now() + timedelta(seconds=self.interval_seconds)
        logger.info(f"🔁 Следующий запуск: {next_run_time:%Y-%m-%d %H:%M:%S}")

    async def start(self):
        """Запуск основного цикла."""
        while not self._stop_event.is_set():
            await self.run_once()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                continue  # интервал истёк — идём на следующий запуск

    def stop(self):
        """Остановка цикла."""
        self._stop_event.set()