import asyncio
from datetime import datetime, timedelta

from core.bot import bot
from settings import settings
from core.logger import filter_futures_logger

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
        """Твоя основная задача."""
        filter_futures_logger.info("🛠 Скачиваем данные...")

        # Скачиваем данные с биржи Binance
        fetcher = AsyncCryptoDataFetcher(save_dir="data/klines")
        futures = fetcher.load_futures_from_json(path='data/all_futures.json')

        fetcher.prepare_folders(["1h"])
        combined_data = await fetcher.download_price(futures, ["1h"], limit=75, save=True)
        filter_futures_logger.info('Данные были скачаны!')

        # Анализ с помощью изоляционного леса
        filter_futures_logger.info("Фильтруем фьючерсы...")
        df_vol = volumes_table(combined_data, tf="1h", bars=72)
        detector = AnomalyDetector(contamination=0.05)
        result = detector.run(df_vol, columns="ALL", direction='up')
        new_list_futures = result[result['is_anomaly']].index

        # Изменяем в базе список фьючерсов
        object_futures = await Futures.get(id=1)
        old_list_futures = object_futures.futures
        if not new_list_futures.empty:
            await object_futures.update(futures=new_list_futures.tolist())

        # Отправляем сообщения администраторам
        text = t.format_futures_update(old_list_futures, new_list_futures.tolist() if not new_list_futures.empty else [])
        for user_id in settings.bot.ADMINS:
            try:
                await bot.send_message(chat_id=user_id, text=text)
            except Exception as e:
                filter_futures_logger.warning(f"Не удалось отправить сообщение админу {user_id}: {e}")

        filter_futures_logger.info("✅ Задача выполнена, фьючерсы заменены!")


    async def run_once(self):
        """Выполнить задачу один раз с логированием."""
        start_time = datetime.now()
        filter_futures_logger.info(f"🚀 Запуск задачи: {start_time:%Y-%m-%d %H:%M:%S}")

        try:
            await self.task()
        except Exception as e:
            filter_futures_logger.exception(f"❌ Ошибка при выполнении задачи: {e}")

        next_run_time = datetime.now() + timedelta(seconds=self.interval_seconds)
        filter_futures_logger.info(f"🔁 Следующий запуск: {next_run_time:%Y-%m-%d %H:%M:%S}")

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