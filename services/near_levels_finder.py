import asyncio

from core.bot import bot
from settings import settings
from core.logger import va_futures_logger as logger

import utils.user.futures_selection as u
from db.psql.models.models import VAFuturesData


class VAProximityScanner:
    """
    Класс для поиска фьючерсов, чья цена находится близко к важным уровням VA.
    Используется для генерации сигналов и уведомлений.
    """

    def __init__(self, interval_minutes: int = 30, proximity_percent: float = 0.5):
        """
        :param interval_minutes: интервал проверки в минутах
        :param proximity_percent: допустимое расстояние от уровня (в %)
        """
        self.interval = interval_minutes * 60
        self.proximity = proximity_percent
        self._running = False

    async def start(self):
        """Основной фоновый цикл"""
        self._running = True
        logger.info("🚀 Запуск VA Proximity Scanner...")

        while self._running:
            try:
                await self.loop()
            except Exception as e:
                logger.error(f"Ошибка в VA Proximity Scanner: {e}")
                await asyncio.sleep(10)

    async def loop(self):
        """Один цикл проверки"""
        logger.info("🔎 Проверка близости цен к уровням VA...")
        await self.check_proximity()

        logger.info(f"💤 Следующая проверка через {self.interval // 60} минут.")
        await asyncio.sleep(self.interval)

    async def check_proximity(self):
        """
        Поиск фьючерсов, чья текущая цена близка к уровням VA.
        """
        futures_data = await VAFuturesData.all()
        if not futures_data:
            logger.warning("⚠️ Нет данных о VA-уровнях.")
            return

        near_levels = []

        # Цены всех фьючерсов
        all_futures_prices = await u.fetcher.get_futures_prices()
        for record in futures_data:
            tf = record.timeframe
            symbol = record.futures
            current_price = all_futures_prices.get(symbol)
            levels = record.info or []

            for level in levels:
                if not isinstance(level, dict):
                    continue

                for key in ["POC", "VAH", "VAL"]:
                    level_price = level.get(key)
                    if not level_price:
                        continue

                    diff_percent = abs((current_price - level_price) / level_price * 100)

                    if diff_percent <= self.proximity:
                        near_levels.append((symbol, key, tf, level_price, current_price, diff_percent))
                        logger.info(f"🎯 {symbol} ({tf}): {current_price} близко к {key}={level_price} ({diff_percent:.2f}%)")

        if not near_levels:
            logger.info("📉 Нет фьючерсов, близких к уровням.")
            return
        else:
            await self.notify_admins(near_levels)

    async def notify_admins(self, near_levels: list):
        """
        Отправка уведомления администраторам о найденных фьючерсах.
        """
        text_lines = ["📊 <b>Фьючерсы, близкие к важным уровням:</b>\n"]

        for symbol, key, tf, level_price, current_price, diff_percent in near_levels:
            text_lines.append(
                f"• <b>{symbol} ({tf})</b> — текущая {current_price:.4f}, уровень {key}={level_price:.4f}"
                f"({diff_percent:.2f}% от уровня)\n"
            )

        text = "\n".join(text_lines)

        for admin_id in settings.bot.ADMINS:
            try:
                await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение админу {admin_id}: {e}")

        logger.info("✅ Уведомления о близких уровнях отправлены!")

    def stop(self):
        """Останавливает фоновую задачу"""
        logger.info("🛑 Остановка VA Proximity Scanner...")
        self._running = False