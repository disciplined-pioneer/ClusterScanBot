from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_timeframes_message(futures_name: str) -> str:
    return (
        f'Вы выбрали фьючерс <i><b>"{futures_name}"</b></i>\n\n'
        'Пожалуйста, выберите таймфрейм для анализа:'
    )

def get_timeframes_keyboard(selected_timeframes: list[str] = None) -> InlineKeyboardMarkup:
    
    if selected_timeframes is None:
        selected_timeframes = []

    timeframes = ['1d', '4h', '1h', '30m', '15m', '5m']

    buttons = []
    for tf in timeframes:
        prefix = "✅ " if tf in selected_timeframes else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{tf}", callback_data=f'time_frame:{tf}')])

    # В одну строку "Начать анализ" и "Выбрать всё"
    action_buttons = [
        InlineKeyboardButton(text="▶️ Начать анализ", callback_data="start_analysis"),
        InlineKeyboardButton(text="⚡ Выбрать всё", callback_data="select_all")
    ]
    buttons.append(action_buttons)

    # Кнопка меню отдельным рядом
    buttons.append([InlineKeyboardButton(text="🔙 Меню", callback_data="go_menu_user")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)