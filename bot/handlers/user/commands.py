from aiogram import Router, types, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.bot import bot
from settings import settings

import bot.keyboards.user.commands as k
import bot.templates.user.commands as t

from bot.filters.user import NewUser
from db.psql.models.models import Users


router = Router()
router.message.filter(F.chat.type == "private")


# Новый пользователь
@router.message(Command("start"), NewUser())
async def new_user_start(message: Message, state: FSMContext):

    # Очистка истории сообщений
    if message.from_user.id not in settings.bot.ADMINS:
        return
    
    # Добавляем в БД
    await message.delete()
    tg_id = message.from_user.id
    username = message.from_user.username
    await Users.create(tg_id=tg_id, username=username)

    await message.answer(
        text=t.start_user_msg,
        reply_markup=k.futures_menu
    )
    await state.clear()


# Старый пользователь
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """
    /start command
    :param msg: Message
    :param state: FSMContext
    :return:
    """
    # Очистка истории сообщений
    if message.from_user.id not in settings.bot.ADMINS:
        return

    await message.delete()
    await message.answer(
        text=t.start_user_msg,
        reply_markup=k.futures_menu
    )

    await state.clear()


# Обработка кнопки "Меню"
@router.callback_query(F.data == "go_menu_user")
async def go_menu_user(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.edit_text(
        text=t.start_user_msg,
        reply_markup=k.futures_menu
    )
    await state.clear()