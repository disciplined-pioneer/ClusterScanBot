from core.bot import bot
from settings import settings
from datetime import datetime

from aiogram.types import ForumTopic
from db.models.models import UserTopics


# Создание топика
async def create_topic(user: str) -> int:

    # Выбираем имя для топика
    if user.username:
        topic_name = f"@{user.username}"
    else:
        topic_name = user.first_name

    topic: ForumTopic = await bot.create_forum_topic(
        chat_id=settings.bot.GROUP_ID,
        name=topic_name
    )
    
    # Сообщение админу
    topic_id = topic.message_thread_id
    await bot.send_message(
        chat_id=settings.bot.GROUP_ID,
        text=f"Пользователь: {topic.name}\nID: {user.id}\n❗️ Оставил новую заявку",
        message_thread_id=topic_id
    )

    # Добавляем информацию в таблицу
    await UserTopics.create(tg_id=user.id,
                            topic_id=topic_id,
                            created_at=datetime.now())
    return topic_id