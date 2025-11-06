import os
import asyncio
from datetime import datetime
from aiogram.types import FSInputFile

from core.bot import bot
from core.logger import va_futures_logger as logger

from db.psql.models.models import VAFuturesData


class VAFuturesReporter:
    """
    Класс для фонового мониторинга VA фьючерсов.
    Проверяет уведомления и выполняет поиск VA раз в час.
    """

    def __init__(self, interval_hours: int = 1):
        self.interval = interval_hours * 60 * 60  # интервал в секундах
        self._running = False

    async def start(self):
        """
        Главный цикл VA-репортера.
        """
        self._running = True
        logger.info("🚀 Запуск VA-репортера...")
        while self._running:
            try:
                await self.loop()
            except Exception as e:
                logger.error(f"Произошла ошибка в VA-цикле: {e}")
                await asyncio.sleep(10)  # защита от бесконечного краша

    async def loop(self):
        """
        Один цикл VA-анализа.
        """
        logger.info("🔍 Начало проверки VA фьючерсов...")
        await self.search_va()

        logger.info(f"🔁 Ожидание {self.interval // 3600} часов до следующей проверки.")
        await asyncio.sleep(self.interval)

    async def search_va(self):
        """
        Поиск VA фьючерсов.
        """
        logger.info("⚙️ Выполняется поиск VA фьючерсов...")



        logger.info("✅ Поиск VA завершён.")

    def stop(self):
        """
        Останавливает цикл репортера.
        """
        logger.info("🛑 Остановка VA-репортера...")
        self._running = False