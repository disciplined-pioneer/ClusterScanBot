import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.user.futures_selection import ALL_LIST_TIMEFRAMES


go_menu_user = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Меню", callback_data="go_menu_user")]
    ]
)

async def get_objects_keyboard(page: int = 0, OBJECTS_PER_PAGE: int = 9, list_futures: list=[], callback: str='futures:', back: bool=True):

    """Меню с пагинацией — выбора фьючерса"""

    if not list_futures:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="go_menu_user")]])

    total_items = len(list_futures)
    total_pages = math.ceil(total_items / OBJECTS_PER_PAGE)

    start = page * OBJECTS_PER_PAGE
    end = start + OBJECTS_PER_PAGE

    buttons = [
        [InlineKeyboardButton(
            text=str(fut),
            callback_data=f"{callback}{fut}"
        )]
        for i, fut in enumerate(list_futures[start:end], start=start)
    ]

    nav_buttons = []
    has_prev = page > 0
    has_next = end < len(list_futures)

    # Кнопка Назад
    if has_prev:
        nav_buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"page:{page - 1}"))

    # Кнопка Вперёд
    if has_next:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"page:{page + 1}"))

    page_button = InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")

    if has_prev and has_next:
        # Обе кнопки есть — номер посередине
        buttons.append([
            nav_buttons[0],
            page_button,
            nav_buttons[1]
        ])
    elif has_prev or has_next:
        # Только одна кнопка — номер страницы над кнопкой
        buttons.append([page_button])
        buttons.append(nav_buttons)

    if back:
        buttons.append([InlineKeyboardButton(text="🔙 Меню", callback_data="go_menu_user")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_timeframes_keyboard(selected_timeframes: list[str] = None, callback_back: str='list_futures', back: bool=True) -> InlineKeyboardMarkup:

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
    if back:
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=callback_back)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)