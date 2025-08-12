from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

futures_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Список фьючерсов", callback_data="list_futures")],
        [InlineKeyboardButton(text="Ввести фьючерс", callback_data="enter_futures")]
    ]
)