from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

import utils.user.update_futures as u
import bot.templates.user.update_futures as t


router = Router()


# Обработка кнопки "Обновить фьючерсы"
@router.callback_query(F.data == "update_futures")
async def update_futures(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()
    try:
        await callback.message.edit_text(t.updating_futures_msg)
        await u.scheduler.task()
        await callback.message.edit_text(t.futures_updated_msg)

    except Exception as e:
        await callback.message.edit_text(f'❌ Ошибка при отборе фьючерсов: {e}')