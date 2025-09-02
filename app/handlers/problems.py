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
from app.google_sheets import gs_logger


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
    await gs_logger.log_event(  # Добавляем логирование
        "Сообщение о проблеме",
        message.from_user.id,
        sent_message.message_id,
        message.caption if message.caption else "Фото без описания"
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
    # Проверяем, что это сообщение о проблеме
    if not callback.message.caption or not callback.message.caption.startswith("⚠️ Сообщение о проблеме"):
        await callback.answer("Это не сообщение о проблеме!")
        return
    
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
    
    await gs_logger.log_event(  # Добавляем логирование
        "Проблема решена",
        callback.from_user.id,
        callback.message.message_id
    )
    

# Обработчик ответов на сообщения о проблемах
@router.message(F.chat.type != ChatType.PRIVATE, F.reply_to_message)
async def handle_problem_solution(message: Message):
    replied_message = message.reply_to_message
    # Проверяем, что это ответ на сообщение о проблеме

    if not replied_message.caption or not replied_message.caption.startswith("⚠️"):
        return
    
    # await messga.answer()
    if (message.from_user and 
        message.from_user.is_bot):
        return
    
    
    # Формируем ссылку на ответное сообщение
    chat = await message.bot.get_chat(GROUP_ID)
    if chat.username:
        message_link = f"https://t.me/{chat.username}/{message.message_id}"
    else:
        # Для групп без username формируем ссылку через ID
        chat_id = str(chat.id).replace('-100', '')
        message_link = f"https://t.me/c/{chat_id}/{message.message_id}"
    
    # Обновляем сообщение о проблеме
    new_caption = replied_message.caption
    
    # Проверяем, не добавлена ли уже ссылка на решение
    if "📸 Решение:" not in new_caption:
        new_caption += f"\n\n📸 Решение: {message_link}"
    
    try:
        await message.bot.unpin_chat_message(
            chat_id=GROUP_ID,
            message_id=replied_message.message_id
        )
        await message.bot.edit_message_caption(
            chat_id=GROUP_ID,
            message_id=replied_message.message_id,
            caption=new_caption,
            parse_mode=ParseMode.HTML
        )
        
        text = message.text if message.text else message.caption
        
        await gs_logger.log_event(  # Добавляем логирование
            "Проблема решена",
            message.from_user.id,
            message.message_id,
            text
        )
    except Exception as e:
        print(f"Не удалось обновить сообщение о проблеме: {e}")