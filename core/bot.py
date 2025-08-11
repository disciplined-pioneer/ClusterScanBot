from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from settings import settings

bot = Bot(
    token=settings.bot.TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)