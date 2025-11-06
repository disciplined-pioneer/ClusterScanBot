import logging
import asyncio
from aiogram import Dispatcher
from aiogram.types import BotCommandScopeDefault

from core.bot import bot
from bot.handlers import routers

from settings import settings
from db.psql.crud.base import init_postgres

from services.futures_update import TaskScheduler
from services.va_futures_reporter import VAFuturesReporter


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

dp = Dispatcher()
dp.include_routers(*routers)


# Классы с фоновыми задачами
reporter = VAFuturesReporter()
scheduler = TaskScheduler(interval_hours=6)


async def main():

    await init_postgres()
    await bot.set_my_commands(
        commands=settings.bot.COMMANDS,
        scope=BotCommandScopeDefault()
    )
    
    asyncio.create_task(scheduler.start()) # Список аномальных фьючерсов
    asyncio.create_task(reporter.start()) # Поиск VA у фьючерсов

    await dp.start_polling(bot)


if __name__ == "__main__":
    
    try:
        logging.info("✅ Бот запущен!")
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.error("🛑 Бот остановлен вручную!")
        scheduler.stop()

    except Exception as e:
        logging.error(f"❌ Возникла критическая ошибка: {type(e).__name__}: {e}")
        scheduler.stop()