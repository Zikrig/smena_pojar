import os
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.enums import ParseMode

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard, get_resolved_keyboard
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
    
    # Отправляем обработанное фото в группу с кнопкой "решено"
    output_file = FSInputFile(output_path)
    
    caption = f"⚠️ Сообщение о проблеме\n⏰ Время: {current_time}"
    if message.caption:
        caption += f"\n📝 Описание: {message.caption}"
    
    # Отправляем сообщение с кнопкой
    sent_message = await message.bot.send_photo(
        chat_id=GROUP_ID,
        photo=output_file,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=get_resolved_keyboard()
    )
    
    # Прикрепляем (закрепляем) сообщение в группе
    try:
        await message.bot.pin_chat_message(
            chat_id=GROUP_ID,
            message_id=sent_message.message_id
        )
    except Exception as e:
        print(f"Не удалось закрепить сообщение: {e}")
    
    # Удаляем временные файлы
    os.remove(input_path)
    os.remove(output_path)
    
    await state.clear()
    await message.answer("✅ Сообщение о проблеме отправлено и закреплено в группе!", reply_markup=get_main_keyboard())

# Обработчик для кнопки "решено"
@router.callback_query(F.data == "resolve_problem")
async def handle_problem_resolved(callback: CallbackQuery):
    # Обновляем сообщение - убираем кнопку и добавляем пометку
    new_caption = callback.message.caption + "\n\n✅ РЕШЕНО"
    
    try:
        # Открепляем сообщение
        await callback.bot.unpin_chat_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
    except Exception as e:
        print(f"Не удалось открепить сообщение: {e}")
    
    # Редактируем сообщение
    await callback.message.edit_caption(
        caption=new_caption,
        parse_mode=ParseMode.HTML,
        reply_markup=None  # Убираем кнопку
    )
    
    await callback.answer("Проблема отмечена как решенная!")