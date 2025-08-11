from aiogram.types import Message
from aiogram.filters import BaseFilter

from db.psql.models.models import Users


class NewUser(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        """
        Проверить пользователя в базе данных
        :param msg: Сообщение
        :return: bool
        """
        user_id = await Users.check(tg_id=msg.from_user.id)
        return not bool(user_id)
