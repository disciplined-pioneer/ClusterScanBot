from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext


router = Router()


# Удаление сообщений, не подключённых к состоянию
@router.message()
async def handle_unexpected_message(message: types.Message, state: FSMContext):
    print('🛑 Удаляем сообщение - не в состоянии 🛑')
    await message.delete()    