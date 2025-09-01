from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext

from app.keyboards import get_main_keyboard
from app.states import Form

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать! Выберите действие:",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "cancel_action")
async def handle_inline_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Действие отменено", reply_markup=get_main_keyboard())
    await callback.answer()
    
@router.callback_query(F.data == "cancel_action")
async def handle_inline_cancel(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.patrol_selection:
        # Особый случай - нужно просто очистить состояние без сообщения
        await state.clear()
        await callback.message.edit_text("Действие отменено")
    else:
        await state.clear()
        await callback.message.answer("Действие отменено", reply_markup=get_main_keyboard())
    await callback.answer()