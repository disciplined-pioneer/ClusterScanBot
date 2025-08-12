import asyncio
from aiogram.types import Message
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from core.bot import bot
import utils.user.futures_selection as u
import bot.keyboards.user.futures_selection as k
import bot.templates.user.futures_selection as t


router = Router()


# Обработка кнопки "Список фьючерсов"
@router.callback_query(F.data == "list_futures")
async def list_futures(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.edit_text(
        text=t.futures_selection_msg,
        reply_markup=await k.get_objects_keyboard()
    )


# Обработка кнопки "Ввести фьючерс"
@router.callback_query(F.data == "enter_futures")
async def enter_futures(callback: types.CallbackQuery, state: FSMContext):

    new_msg = await callback.message.edit_text(
        text=t.enter_futures_msg,
        reply_markup=k.go_menu_user
    )
    await state.update_data(last_id_msg=new_msg.message_id)
    await state.set_state(u.FuturesStates.futures_name)


# Обработка введённого фьючерса
@router.message(StateFilter(u.FuturesStates.futures_name), F.text)
async def received_futures_name(message: Message, state: FSMContext):

    # Данные
    await message.delete()
    data = await state.get_data()
    last_id_msg = data.get('last_id_msg')

    # Проверка фьючерса на корректность
    futures_name, error_text = u.check_futures_presence(message.text)
    try:
        if error_text:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=last_id_msg,
                text=error_text,
                reply_markup=k.go_menu_user
            )
            await state.set_state(u.FuturesStates.futures_name)
            return
    except:
        return
    
    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=last_id_msg,
        text=t.format_timeframes_message(futures_name),
        reply_markup=k.get_timeframes_keyboard(callback_back='enter_futures')
    )

    await state.update_data(futures_name=futures_name)


# Обработка кнопок пагинации
@router.callback_query(F.data.startswith("page:"))
async def pagination_handler(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])  # получаем номер страницы
    markup = await k.get_objects_keyboard(page=page)

    await callback.message.edit_reply_markup(reply_markup=markup) 
    await callback.answer() 


# Обработка выбранного фьючерса
@router.callback_query(F.data.startswith("futures:"))
async def futures_choice(callback: types.CallbackQuery, state: FSMContext):

    futures_name = callback.data.split(':')[1]

    await callback.message.edit_text(
        text=t.format_timeframes_message(futures_name),
        reply_markup=k.get_timeframes_keyboard()
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
        reply_markup=k.get_timeframes_keyboard(list_timeframes)
    )


# Обработка выбора всех таймфреймов
@router.callback_query(F.data == "select_all")
async def select_all_futures(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()
    list_timeframes = set(k.ALL_LIST_TIMEFRAMES)  # множество для чистоты данных

    await state.update_data(list_timeframes=list(list_timeframes))

    await callback.message.edit_reply_markup(
        reply_markup=k.get_timeframes_keyboard(list(list_timeframes))
    )


# Начало работы анализа
@router.callback_query(F.data == "start_analysis")
async def start_analysis(callback: types.CallbackQuery, state: FSMContext):

    # Проверка на наличие хотябы 1 фьючерса
    data = await state.get_data()
    list_timeframes = data.get('list_timeframes', [])

    if not list_timeframes:
        await callback.answer(
            text=t.select_timeframe_msg,
            show_alert=True
        )
        return


    await callback.message.edit_text(t.start_data_collection_msg)
    await asyncio.sleep(1)

    await callback.message.edit_text(t.data_collection_finished_msg)
    await asyncio.sleep(1)

    await callback.message.edit_text(t.futures_analyzed_msg)
    await asyncio.sleep(1)
    
    await state.clear()