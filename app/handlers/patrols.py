import os
from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.enums import ParseMode
from aiogram.filters import or_f
from aiogram.types import CallbackQuery

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard, get_patrol_keyboard, get_patrol_in_progress_keyboard
from app.image_processor import ImageProcessor
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.google_sheets import gs_logger
from app.keyboards import get_resolved_keyboard

router = Router()

async def process_problem_photo(message: Message, state: FSMContext, problem_description: str = None):
    data = await state.get_data()
    patrol_type = data.get('patrol_type', 'Обход')
    
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    input_path = f"app/data/temp_{file_id}.jpg"
    await message.bot.download_file(file.file_path, destination=input_path)

    current_time = get_moscow_time().strftime("%Y-%m-%d %H:%M:%S")
    output_path = f"app/data/output_{file_id}.jpg"

    processor = ImageProcessor()
    processor.add_text_with_outline(input_path, output_path, current_time)

    output_file = FSInputFile(output_path)

    caption = (
        f"⚠️ Сообщение о проблеме (при {patrol_type})\n"
        f"⏰ Время: {current_time}"
    )
    if problem_description:
        caption += f"\n📝 Описание: {problem_description}"
    elif message.caption:
        caption += f"\n📝 Описание: {message.caption}"

    sent_message = await message.bot.send_photo(
        chat_id=GROUP_ID,
        photo=output_file,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=get_resolved_keyboard()
    )

    try:
        await message.bot.pin_chat_message(GROUP_ID, sent_message.message_id)
    except Exception as e:
        print(f"Не удалось закрепить сообщение: {e}")

    os.remove(input_path)
    os.remove(output_path)

    await gs_logger.log_event(
        "Сообщение о проблеме",
        message.from_user.id,
        sent_message.message_id,
        problem_description if problem_description else (message.caption if message.caption else "Фото без описания")
    )

    return sent_message

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔄 Обход")
async def handle_patrol_selection(message: Message, state: FSMContext):
    await state.set_state(Form.patrol_selection)
    await message.answer(
        "Выберите объект для обхода:",
        reply_markup=get_patrol_keyboard()
    )

@router.callback_query(Form.patrol_selection, F.data == "patrol_base1")
async def handle_base1_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.base1_patrol)
    await state.update_data(photo_paths=[], patrol_type="Обход Базы 1", problems=[])
    await callback.message.answer(
        "🔄 Начало обхода Базы 1\n\n"
        "Делайте фото потенциально пожароопасных мест и отправляйте их.\n"
        "При обнаружении проблемы нажмите кнопку \"❗️ Нарушение\".\n"
        "По окончании обхода нажмите кнопку \"Завершить обход\".",
        reply_markup=get_patrol_in_progress_keyboard()
    )
    await callback.answer()

@router.callback_query(Form.patrol_selection, F.data == "patrol_atp")
async def handle_atp_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.atp_patrol)
    await state.update_data(photo_paths=[], patrol_type="Обход АТП", problems=[])
    await callback.message.answer(
        "🔄 Начало обхода АТП\n\n"
        "Делайте фото потенциально пожароопасных мест и отправляйте их.\n"
        "При обнаружении проблемы нажмите кнопку \"❗️ Нарушение\".\n"
        "По окончании обхода нажмите кнопку \"Завершить обход\".",
        reply_markup=get_patrol_in_progress_keyboard()
    )
    await callback.answer()

@router.callback_query(Form.patrol_selection, F.data == "patrol_base2")
async def handle_base2_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.base2_patrol)
    await state.update_data(photo_paths=[], patrol_type="Обход Базы 2", problems=[])
    await callback.message.answer(
        "🔄 Начало обхода Базы 2\n\n"
        "Делайте фото потенциально пожароопасных мест и отправляйте их.\n"
        "При обнаружении проблемы нажмите кнопку \"❗️ Нарушение\".\n"
        "По окончании обхода нажмите кнопку \"Завершить обход\".",
        reply_markup=get_patrol_in_progress_keyboard()
    )
    await callback.answer()

async def add_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_paths = data.get('photo_paths', [])
    
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    input_path = f"app/data/temp_{file_id}.jpg"
    await message.bot.download_file(file.file_path, destination=input_path)

    current_time = get_moscow_time()
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    output_path = f"app/data/output_{file_id}.jpg"

    processor = ImageProcessor()
    processor.add_text_with_outline(input_path, output_path, current_time_str)

    photo_paths.append({
        'path': output_path,
        'time': current_time
    })
    await state.update_data(photo_paths=photo_paths)

    os.remove(input_path)
    await message.answer("Фото добавлено в обход. Продолжайте или завершите обход.", reply_markup=get_patrol_in_progress_keyboard())

@router.callback_query(
    or_f(Form.base1_patrol, Form.atp_patrol, Form.base2_patrol), 
    F.data == "report_problem"
)
async def handle_problem_report(callback: CallbackQuery, state: FSMContext):
    previous_state = await state.get_state()
    await state.update_data(previous_state=previous_state)
    await state.set_state(Form.patrol_problem)
    await callback.message.answer(
        "Сделайте ФОТО проблемы и отправьте его. Можете добавить ТЕКСТ в подписи к фото:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(Form.patrol_problem, F.photo)
async def handle_problem_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    patrol_type = data.get('patrol_type', 'Обход')

    description = message.caption if message.caption else "Фото без описания"
    await process_problem_photo(message, state, description)

    problems = data.get('problems', [])
    problems.append(description)
    await state.update_data(problems=problems)

    previous_state = data.get("previous_state")
    if previous_state:
        await state.set_state(previous_state)
    
    await message.answer(
        "Проблема зафиксирована. Продолжайте обход или завершите его.",
        reply_markup=get_patrol_in_progress_keyboard()
    )

@router.callback_query(
    or_f(Form.base1_patrol, Form.atp_patrol, Form.base2_patrol), 
    F.data == "finish_patrol"
)
async def handle_finish_patrol(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_paths = data.get('photo_paths', [])
    problems = data.get('problems', [])
    patrol_type = data.get('patrol_type', 'Обход')
    
    
    if not photo_paths:
        await callback.message.answer("Нет фото для отправки.", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    await callback.answer()

    media = []
    caption = f"{patrol_type} завершен\n\n"
    caption += "Время фото:\n"
    for i, photo_data in enumerate(photo_paths, 1):
        photo_time = photo_data['time'].strftime("%Y-%m-%d %H:%M:%S")
        caption += f"{i}. {photo_time}\n"
    
    if problems:
        caption += "\nОбнаружены проблемы:\n"
        for i, problem in enumerate(problems, 1):
            caption += f"{i}. {problem}\n"

    for i, photo_data in enumerate(photo_paths):
        if i == 0:
            media.append(types.InputMediaPhoto(
                media=FSInputFile(photo_data['path']),
                caption=caption
            ))
        else:
            media.append(types.InputMediaPhoto(
                media=FSInputFile(photo_data['path'])
            ))

    sent_messages = await callback.bot.send_media_group(
        chat_id=GROUP_ID,
        media=media
    )

    await gs_logger.log_event(
        patrol_type,
        callback.from_user.id,
        sent_messages[0].message_id,
        "Проблемы: " + ", ".join(problems) if problems else "Успешно"
    )
    
    for photo_data in photo_paths:
        if os.path.exists(photo_data['path']):
            os.remove(photo_data['path'])
    
    await state.clear()
    await callback.message.answer(
        f"✅ {patrol_type} завершен! Все фото отправлены в группу.",
        reply_markup=get_main_keyboard()
    )

@router.message(
    or_f(Form.base1_patrol, Form.atp_patrol, Form.base2_patrol),
    F.photo
)
async def handle_patrol_photo(message: Message, state: FSMContext):
    await add_patrol_photo(message, state)