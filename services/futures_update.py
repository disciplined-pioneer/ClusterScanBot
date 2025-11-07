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

    def __init__(self, interval_hours: int = 6):
        """
        Планировщик задач.
        :param interval_hours: Интервал в часах между запусками задачи.
        """
        self.interval_hours = interval_hours
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
        # scale_by='row' → стандартизация по строкам (по каждому фьючерсу)
        df_vol = volumes_table(combined_data, tf="15m", bars=288)
        detector = AnomalyDetector(contamination=0.1, scale_by='row')
        result = detector.run(df_vol, columns="ALL", direction='up')

        # Изменяем в базе список фьючерсов
        new_list_futures = result[result['is_anomaly']].index.tolist()
        object_futures = await Futures.get(id=1)
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

    async def start(self):
        """Запуск основного цикла с синхронизацией по времени."""

        # Сначала запускаем задачу сразу
        await self.run_once()

        while not self._stop_event.is_set():
            now = datetime.now()

            # Вычисляем следующий «ровный» час интервала (0,6,12,18)
            next_hour = (now.hour // self.interval_hours + 1) * self.interval_hours
            next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=next_hour)

            # Если время ушло за сутки, переносим на следующий день
            if next_run <= now:
                next_run += timedelta(hours=self.interval_hours)

            sleep_seconds = (next_run - now).total_seconds()
            logger.info(f"⏳ Ждём до следующего запуска: {next_run:%Y-%m-%d %H:%M:%S} ({sleep_seconds:.0f} секунд)")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_seconds)
            except asyncio.TimeoutError:
                await self.run_once()

    def stop(self):
        """Остановка цикла."""
        self._stop_event.set()
