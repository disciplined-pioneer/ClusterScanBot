from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

import bot.templates.user.futures_selection as t


router = Router()


# Обработка выбранного фьючерса
@router.callback_query(F.data.startswith("futures:"))
async def futures_choice(callback: types.CallbackQuery, state: FSMContext):

    futures_name = callback.data.split(':')[1]

    await callback.message.edit_text(
        text=t.format_timeframes_message(futures_name),
        reply_markup=t.get_timeframes_keyboard()
    )

    await state.update_data(futures_name=futures_name)