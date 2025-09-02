import os
from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.enums import ParseMode

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard, get_patrol_keyboard
from app.image_processor import ImageProcessor
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.google_sheets import gs_logger


router = Router()

# Добавим новый импорт
from aiogram.types import CallbackQuery

# Добавим новый обработчик для кнопки "Обход"
@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔄 Обход")
async def handle_patrol_selection(message: Message, state: FSMContext):
    await state.set_state(Form.patrol_selection)
    await message.answer(
        "Выберите объект для обхода:",
        reply_markup=get_patrol_keyboard()
    )

# Добавим обработчики для инлайн-кнопок
@router.callback_query(Form.patrol_selection, F.data == "patrol_base1")
async def handle_base1_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.base1_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 1")
    await callback.message.answer(
        "🔄 Обход Базы 1 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(Form.patrol_selection, F.data == "patrol_atp")
async def handle_atp_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.atp_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход АТП")
    await callback.message.answer(
        "🔄 Обход АТП - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(Form.patrol_selection, F.data == "patrol_base2")
async def handle_base2_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.base2_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 2")
    await callback.message.answer(
        "🔄 Обход Базы 2 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()
    
async def process_patrol_photo(message: Message, state: FSMContext, patrol_type: str):
    data = await state.get_data()
    current_step = data.get('patrol_step', 1)
    photo_paths = data.get('photo_paths', [])
    
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
    
    # Сохраняем путь к обработанному фото
    photo_paths.append(output_path)
    await state.update_data(photo_paths=photo_paths)
    
    # Удаляем временный файл
    os.remove(input_path)
    
    # Переходим к следующему шагу или завершаем
    if current_step < 5:
        next_step = current_step + 1
        await state.update_data(patrol_step=next_step)
        await message.answer(
            f"🔄 {patrol_type} - Метка {next_step}:\n"
            "1. Нажмите «📎»\n"
            "2. Выберите «Сделать фото»\n"
            "3. Сделайте фото на метке {next_step}\n"
            "4. Отправьте фото",
            reply_markup=get_cancel_keyboard()
        )
    else:
        # Отправляем все фото одним сообщением
        media = []
        for i, photo_path in enumerate(photo_paths, 1):
            media.append(types.InputMediaPhoto(
                media=FSInputFile(photo_path),
                caption=f"{patrol_type} - Метка {i}\n⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" if i == 1 else None
            ))
        
        sent_message = await message.bot.send_media_group(
            chat_id=GROUP_ID,
            media=media
        )
        
        # Удаляем все временные файлы
        for photo_path in photo_paths:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        await state.clear()
        await message.answer(f"✅ {patrol_type} завершен! Все фото отправлены в группу.", reply_markup=get_main_keyboard())
            
        await gs_logger.log_event(  # Добавляем логирование
            "Звонок в пожарную часть",
            message.from_user.id,
            sent_message[0].message_id
        )

@router.message(F.text == "🔄 Обход Базы 1")
async def handle_base1_patrol(message: Message, state: FSMContext):
    await state.set_state(Form.base1_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 1")
    await message.answer(
        "🔄 Обход Базы 1 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.base1_patrol, F.photo)
async def handle_base1_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await process_patrol_photo(message, state, data.get('patrol_type', 'Обход Базы 1'))

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔄 Обход АТП")
async def handle_atp_patrol(message: Message, state: FSMContext):
    await state.set_state(Form.atp_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход АТП")
    await message.answer(
        "🔄 Обход АТП - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.atp_patrol, F.photo)
async def handle_atp_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await process_patrol_photo(message, state, data.get('patrol_type', 'Обход АТП'))

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔄 Обход Базы 2")
async def handle_base2_patrol(message: Message, state: FSMContext):
    await state.set_state(Form.base2_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 2")
    await message.answer(
        "🔄 Обход Базы 2 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.base2_patrol, F.photo)
async def handle_base2_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await process_patrol_photo(message, state, data.get('patrol_type', 'Обход Базы 2'))