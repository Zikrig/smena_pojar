import os
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.enums import ParseMode

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard
from app.image_processor import ImageProcessor
from app.config import GROUP_ID
from app.utils import get_moscow_time

router = Router()

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "⚠️ Проблема")
async def handle_problem_report(message: Message, state: FSMContext):
    await state.set_state(Form.problem_report)
    await message.answer(
        "⚠️ Сообщение о проблеме:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото проблемы\n"
        "4. Добавьте описание в подписи к фото\n"
        "5. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.problem_report, F.photo)
async def handle_problem_report_photo(message: Message, state: FSMContext):
    # Обрабатываем фото с наложением времени
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    input_path = f"app/data/temp_{file_id}.jpg"
    await message.bot.download_file(file.file_path, destination=input_path)
    
    # Накладываем время на фото
    current_time = get_moscow_time().strftime("%Y-%m-%d %H:%M:%S")
    output_path = f"app/data/output_{file_id}.jpg"
    
    processor = ImageProcessor()
    processor.add_text_with_outline(input_path, output_path, current_time)
    
    # Отправляем обработанное фото в группу
    output_file = FSInputFile(output_path)
    
    caption = f"⚠️ Сообщение о проблеме\n⏰ Время: {current_time}"
    if message.caption:
        caption += f"\n📝 Описание: {message.caption}"
    
    await message.bot.send_photo(
        chat_id=GROUP_ID,
        photo=output_file,
        caption=caption,
        parse_mode=ParseMode.HTML
    )
    
    # Удаляем временные файлы
    os.remove(input_path)
    os.remove(output_path)
    
    await state.clear()
    await message.answer("✅ Сообщение о проблеме отправлено в группу!", reply_markup=get_main_keyboard())