import asyncio
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


# Обработка выбранного таймфрейма
@router.callback_query(F.data.startswith("time_frame:"))
async def time_frame_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    list_timeframes = data.get('list_timeframes', [])

    time_frame = callback.data.split(':')[1]

    # Используем set для избежания дубликатов
    selected = set(list_timeframes)
    if time_frame in selected:
        selected.remove(time_frame)
    else:
        selected.add(time_frame)

    list_timeframes = list(selected)
    await state.update_data(list_timeframes=list_timeframes)

    await callback.message.edit_reply_markup(
        reply_markup=t.get_timeframes_keyboard(list_timeframes)
    )


# Обработка всех таймфреймов
@router.callback_query(F.data == "select_all")
async def select_all_futures(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()
    list_timeframes = set(t.ALL_LIST_TIMEFRAMES)  # множество для чистоты данных

    await state.update_data(list_timeframes=list(list_timeframes))

    await callback.message.edit_reply_markup(
        reply_markup=t.get_timeframes_keyboard(list(list_timeframes))
    )


# Начало работы анализа
@router.callback_query(F.data == "start_analysis")
async def start_analysis(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.edit_text(t.start_data_collection_msg)
    await asyncio.sleep(1)

    await callback.message.edit_text(t.data_collection_finished_msg)
    await asyncio.sleep(1)

    await callback.message.edit_text(t.futures_analyzed_msg)
    await asyncio.sleep(1)
    
    await state.clear()