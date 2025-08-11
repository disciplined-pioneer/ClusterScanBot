from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.psql.models.models import Futures

start_user_msg = 'Выберите один из фьючерсов'

async def get_objects_keyboard(page: int = 0, OBJECTS_PER_PAGE: int = 9):

    """Меню с пагинацией — выбор фьючерса"""

    objects = await Futures.get(id=1)
    if not objects or not objects.futures:
        return InlineKeyboardMarkup(inline_keyboard=[])

    list_futures = objects.futures

    start = page * OBJECTS_PER_PAGE
    end = start + OBJECTS_PER_PAGE

    buttons = [
        [InlineKeyboardButton(
            text=str(fut),
            callback_data=f"futures:{fut}"
        )]
        for i, fut in enumerate(list_futures[start:end], start=start)
    ]

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"page:{page - 1}"))
    if end < len(list_futures):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"page:{page + 1}"))

    if nav_buttons:
        buttons.append(nav_buttons)  # навигация — одна строка

    return InlineKeyboardMarkup(inline_keyboard=buttons)
