from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

import bot.templates.user.update_futures as t

from services.report_timer import TaskScheduler


router = Router()
scheduler = TaskScheduler(interval_days=1)


# Обработка кнопки "Обновить фьючерсы"
@router.callback_query(F.data == "update_futures")
async def update_futures(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()
    try:
        await callback.message.edit_text(t.updating_futures_msg)
        await scheduler.task()
        await callback.message.edit_text(t.futures_updated_msg)

    except Exception as e:
        await callback.message.edit_text(f'❌ Ошибка при отборе фьючерсов: {e}')