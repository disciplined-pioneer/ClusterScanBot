import os
import asyncio
from datetime import datetime
from aiogram.types import FSInputFile

from core.bot import bot
from settings import settings
from core.logger import va_futures_logger as logger

from db.psql.models.models import VAFuturesData, Futures

import utils.user.futures_selection as u
from integrations.binance.volume_profile import get_vap_levels


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
        logger.info("🔍 Начало поска VA фьючерсов...")
        await self.search_va()

        logger.info(f"🔁 Ожидание {self.interval // 3600} часов до следующего поиска")
        await asyncio.sleep(self.interval)

    async def search_va(self):
        """
        Поиск VA фьючерсов.
        """
        logger.info("⚙️ Выполняется поиск VA фьючерсов...")

        # Скачиваем данные о ценах
        futures = await Futures.get(id=1)
        if not futures:
            return
        all_futures = futures.futures

        #all_futures = u.fetcher.load_futures_from_json(path='data/all_futures.json')
        combined_data = await u.fetcher.download_price(
            all_futures, ['4h', '1h'], limit=1500, save=False
        )

        # Удаляем старые уровни
        all_va = await VAFuturesData.all()
        for va in all_va:
            await va.delete()

        # Поиск VA в каждом фьючерсе
        for (symbol, tf), df in combined_data.items():
            df = combined_data[(symbol, tf)]
            vap_levels = get_vap_levels(df)
            clean_levels = [item[0] for item in vap_levels if isinstance(item, (list, tuple)) and isinstance(item[0], dict)]

            await VAFuturesData.create(
                futures=symbol,
                timeframe=tf,
                price=df.iloc[-1]['close'],
                percent=0,
                info=clean_levels
            )

        logger.info("✅ Поиск VA завершён")

        for tg_id in settings.bot.ADMINS:
            try:
                await bot.send_message(
                    chat_id=tg_id,
                    text=f'✅ Уровни были успешно обновлены!'
                )
            except:
                pass

    def stop(self):
        """
        Останавливает цикл репортера.
        """
        logger.info("🛑 Остановка VA-репортера...")
        self._running = False