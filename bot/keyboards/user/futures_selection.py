from db.psql.models.models import Futures
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ALL_LIST_TIMEFRAMES = ['1d', '4h', '1h', '30m', '15m', '5m']

go_menu_user = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Меню", callback_data="go_menu_user")]
    ]
)

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

    buttons.append([InlineKeyboardButton(text="🔙 Меню", callback_data="go_menu_user")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_timeframes_keyboard(selected_timeframes: list[str] = None, callback_back: str='list_futures') -> InlineKeyboardMarkup:

    if selected_timeframes is None:
        selected_timeframes = []

    buttons = []
    for tf in ALL_LIST_TIMEFRAMES:
        prefix = "✅ " if tf in selected_timeframes else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{tf}", callback_data=f'time_frame:{tf}')])

    # В одну строку "Начать анализ" и "Выбрать всё"
    action_buttons = [
        InlineKeyboardButton(text="▶️ Начать анализ", callback_data="start_analysis"),
        InlineKeyboardButton(text="⚡ Выбрать всё", callback_data="select_all")
    ]
    buttons.append(action_buttons)

    # Кнопка меню отдельным рядом
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=callback_back)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)