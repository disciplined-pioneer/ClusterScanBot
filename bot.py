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
from services.near_levels_finder import VAProximityScanner


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


dp = Dispatcher()
dp.include_routers(*routers)


# Классы для фоновых задач
reporter = VAFuturesReporter()
scheduler = TaskScheduler(interval_hours=6)
scanner = VAProximityScanner(interval_minutes=5, proximity_percent=5)


async def start_background_tasks():

    # Список аномальных фьючерсов
    task1 = asyncio.create_task(scheduler.start())
    await asyncio.sleep(60)
    
    # Поиск VA у фьючерсов
    task2 = asyncio.create_task(reporter.start())
    await asyncio.sleep(60)

    # Сканнер проверки близости к уровням
    task3 = asyncio.create_task(scanner.start())
    
    await asyncio.gather(task1, task2, task3)


async def main():

    await init_postgres()
    await bot.set_my_commands(
        commands=settings.bot.COMMANDS,
        scope=BotCommandScopeDefault()
    )
    
    asyncio.create_task(start_background_tasks())

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
