import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.google_sheets import gs_logger

router = Router()

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🚨 ЧП")
async def handle_emergency(message: Message, state: FSMContext):
    await state.set_state(Form.emergency)
    await message.answer(
        "🚨 Чрезвычайная ситуация:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото» или «Записать видео»\n"
        "3. Добавьте описание в подписи к медиафайлу\n"
        "4. Отправьте фото или видео",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.emergency, F.photo)
async def handle_emergency_photo(message: Message, state: FSMContext):
    # Получаем текущее время
    current_time = get_moscow_time().strftime("%Y-%m-%d %H:%M:%S")
    
    # Формируем подпись
    caption = f"🚨 Чрезвычайная ситуация\n⏰ Время: {current_time}"
    if message.caption:
        caption += f"\n📝 Описание: {message.caption}"
    
    # Отправляем фото по file_id
    sent_message = await message.bot.send_photo(
        chat_id=GROUP_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        parse_mode=ParseMode.HTML
    )
    
    await state.clear()
    await message.answer("✅ Сообщение о ЧП отправлено в группу!", reply_markup=get_main_keyboard())
    await gs_logger.log_event(
        "Чрезвычайная ситуация (Фото или видео)",
        message.from_user.id,
        sent_message.message_id,
        message.caption if message.caption else "Без описания"
    )

@router.message(Form.emergency, F.video)
async def handle_emergency_video(message: Message, state: FSMContext):
    # Получаем текущее время
    current_time = get_moscow_time().strftime("%Y-%m-%d %H:%M:%S")
    
    # Формируем подпись
    caption = f"🚨 Чрезвычайная ситуация\n⏰ Время: {current_time}"
    if message.caption:
        caption += f"\n📝 Описание: {message.caption}"
    
    # Отправляем видео по file_id
    sent_message = await message.bot.send_video(
        chat_id=GROUP_ID,
        video=message.video.file_id,
        caption=caption,
        parse_mode=ParseMode.HTML
    )
    
    await state.clear()
    await message.answer("✅ Сообщение о ЧП отправлено в группу!", reply_markup=get_main_keyboard())
    await gs_logger.log_event(
        "Чрезвычайная ситуация (Видео)",
        message.from_user.id,
        sent_message.message_id,
        message.caption if message.caption else "Видео без описания"
    )