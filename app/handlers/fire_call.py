from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.enums import ParseMode

from app.states import Form
from app.keyboards import get_fire_call_keyboard, get_main_keyboard
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.google_sheets import gs_logger

router = Router()

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "📞 Звонок в пожарную часть")
async def handle_fire_call(message: Message, state: FSMContext):
    await state.set_state(Form.fire_call)
    await message.answer(
        "📞 Выберите номер для звонка в пожарную часть:",
        reply_markup=get_fire_call_keyboard()
    )

@router.callback_query(Form.fire_call, F.data.startswith("call_"))
async def handle_fire_call_number(callback: CallbackQuery, state: FSMContext):
    number = callback.data.replace("call_", "")
    
    current_time = get_moscow_time().strftime("%H:%M")
    
    await callback.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📞 <b>Звонок в пожарную часть</b>\n⏰ Время: {current_time}\n📞 Номер: {number}",
        parse_mode=ParseMode.HTML
    )
    
    await state.clear()
    sent_message = await callback.message.answer(
        f"✅ Информация о звонке на номер {number} отправлена в группу!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()
    
    await gs_logger.log_event(  # Добавляем логирование
    "Звонок в пожарную часть",
    callback.from_user.id,
    sent_message.message_id
    )