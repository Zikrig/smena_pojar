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
from app.keyboards import get_cancel_keyboard, get_main_keyboard, get_patrol_keyboard, get_patrol_step_keyboard
from app.image_processor import ImageProcessor
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.google_sheets import gs_logger
from app.keyboards import get_resolved_keyboard

router = Router()


async def process_problem_photo(message: Message, state: FSMContext, problem_description: str = None):
    data = await state.get_data()
    patrol_type = data.get('patrol_type', 'Обход')
    current_step = data.get('patrol_step', 1)
    
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
        f"⚠️ Сообщение о проблеме (при {patrol_type}, метка {current_step})\n"
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
        reply_markup=get_resolved_keyboard()   # 🔑 добавляем кнопку
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
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 1", problems={})
    await callback.message.answer(
        "🔄 Обход Базы 1 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото\n"
        "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
        reply_markup=get_patrol_step_keyboard()
    )
    await callback.answer()

@router.callback_query(Form.patrol_selection, F.data == "patrol_atp")
async def handle_atp_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.atp_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход АТП", problems={})
    await callback.message.answer(
        "🔄 Обход АТП - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото\n"
        "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
        reply_markup=get_patrol_step_keyboard()
    )
    await callback.answer()

@router.callback_query(Form.patrol_selection, F.data == "patrol_base2")
async def handle_base2_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.base2_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 2", problems={})
    await callback.message.answer(
        "🔄 Обход Базы 2 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото\n"
        "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
        reply_markup=get_patrol_step_keyboard()
    )
    await callback.answer()
    
async def process_patrol_photo(message: Message, state: FSMContext, patrol_type: str):
    data = await state.get_data()
    current_step = data.get('patrol_step', 1)
    photo_paths = data.get('photo_paths', [])
    problems = data.get('problems', {}) 
    
    # Получаем текущее время для этого конкретного фото
    photo_time = get_moscow_time()
    current_time_str = photo_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Обрабатываем фото с наложением времени
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    input_path = f"app/data/temp_{file_id}.jpg"
    await message.bot.download_file(file.file_path, destination=input_path)
    
    # Накладываем время на фото
    output_path = f"app/data/output_{file_id}.jpg"
    
    processor = ImageProcessor()
    processor.add_text_with_outline(input_path, output_path, current_time_str)
    
    # Сохраняем путь к обработанному фото и время создания
    photo_paths.append({
        'path': output_path,
        'time': photo_time  # Сохраняем объект времени, а не строку
    })
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
            f"3. Сделайте фото на метке {next_step}\n"
            "4. Отправьте фото\n"
            "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
            reply_markup=get_patrol_step_keyboard()
        )
    else:
        # Формируем подпись с учетом проблем
        caption = f"{patrol_type}"
        if problems:
            problem_points = ", ".join([f"метка {k}" for k in problems.keys()])
            # caption += f"\n⚠️ Проблемы на: {problem_points}"
        
        
        # Отправляем медиагруппу
        media = []
        media_caption = ""
        for i, photo_data in enumerate(photo_paths, 1):
            photo_time_str = photo_data['time'].strftime("%Y-%m-%d %H:%M:%S")
            media_caption += f"{caption}\nМетка {i} - {photo_time_str}"
            
            if str(i) in problems:
                media_caption += f"\nПроблема: {problems[str(i)]}"
 
        
        for i, photo_data in enumerate(photo_paths, 1):
            if i == 1:
                media.append(types.InputMediaPhoto(
                    media=FSInputFile(photo_data['path']),
                    caption=media_caption,
                ))
            else:
                media.append(types.InputMediaPhoto(
                    media=FSInputFile(photo_data['path'])
                ))
        
        sent_message = await message.bot.send_media_group(
            chat_id=GROUP_ID,
            media=media
        )

        # Логируем событие
        await gs_logger.log_event(
            patrol_type,
            message.from_user.id,
            sent_message[0].message_id,
            "Проблемы: " + ", ".join(problems.values()) if problems else "Успешно"
        )
        
        # Удаляем все временные файлы
        for photo_data in photo_paths:
            if os.path.exists(photo_data['path']):
                os.remove(photo_data['path'])
        
        await state.clear()
        await message.answer(f"✅ {patrol_type} завершен! Все фото отправлены в группу.", reply_markup=get_main_keyboard())

@router.callback_query(
    or_f(Form.base1_patrol, Form.atp_patrol, Form.base2_patrol), 
    F.data == "report_problem"
)
async def handle_problem_report(callback: CallbackQuery, state: FSMContext):
    previous_state = await state.get_state()
    await state.update_data(previous_state=previous_state)
    
    data = await state.get_data()
    current_step = data.get('patrol_step', 1)
    
    
    await state.set_state(Form.patrol_problem)
    await state.update_data(problem_step=current_step)
    
    await callback.message.answer(
        "Сделайте ФОТО проблемы и отправьте его. Можете добавить ТЕКСТ в подписи к фото:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(Form.patrol_problem, F.photo)
async def handle_problem_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    problem_step = data.get('problem_step')
    patrol_type = data.get('patrol_type', 'Обход')

    description = message.caption if message.caption else "Фото без описания"

    # Отправляем карточку проблемы
    await process_problem_photo(message, state, description)

    # Добавляем фото в обход
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    input_path = f"app/data/temp_{file_id}.jpg"
    await message.bot.download_file(file.file_path, destination=input_path)

    current_time = get_moscow_time()
    output_path = f"app/data/output_{file_id}.jpg"

    processor = ImageProcessor()
    processor.add_text_with_outline(input_path, output_path, current_time.strftime("%Y-%m-%d %H:%M:%S"))

    # Обновляем фото_paths
    photo_paths = data.get('photo_paths', []).copy()
    photo_paths.append({'path': output_path, 'time': current_time})

    # Обновляем problems
    problems = data.get('problems', {}).copy()
    problems[str(problem_step)] = description

    await state.update_data(photo_paths=photo_paths, problems=problems)

    if os.path.exists(input_path):
        os.remove(input_path)

    await message.answer(f"✅ Проблема на метке {problem_step} зафиксирована и учтена в обходе.")

    # Продолжаем обход
    current_step = data.get('patrol_step', 1)
    if current_step < 5:
        next_step = current_step + 1
        await state.update_data(patrol_step=next_step)

        previous_state = data.get("previous_state")
        if previous_state:
            await state.set_state(previous_state)

        await message.answer(
            f"🔄 {patrol_type} - Метка {next_step}:\n"
            "1. Нажмите «📎»\n"
            "2. Выберите «Сделать фото»\n"
            f"3. Сделайте фото на метке {next_step}\n"
            "4. Отправьте фото\n"
            "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
            reply_markup=get_patrol_step_keyboard()
        )
    else:
        # Финализация обхода
        await process_patrol_photo(message, state, patrol_type)


# Добавим обработчик для текстового описания проблемы (если фото отправлено отдельно)
# @router.message(Form.patrol_problem, F.text)
async def handle_problem_description(message: Message, state: FSMContext):
    data = await state.get_data()
    problem_step = data.get('problem_step')
    problems = data.get('problems', {})
    
    problems[str(problem_step)] = message.text
    await state.update_data(problems=problems)
    
    await message.answer(
        "Теперь отправьте фото проблемы:",
        reply_markup=get_cancel_keyboard()
    )
    
@router.message(F.text == "🔄 Обход Базы 1")
async def handle_base1_patrol(message: Message, state: FSMContext):
    await state.set_state(Form.base1_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 1", problems={})
    await message.answer(
        "🔄 Обход Базы 1 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото\n"
        "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
        reply_markup=get_patrol_step_keyboard()
    )

@router.message(Form.base1_patrol, F.photo)
async def handle_base1_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await process_patrol_photo(message, state, data.get('patrol_type', 'Обход Базы 1'))

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔄 Обход АТП")
async def handle_atp_patrol(message: Message, state: FSMContext):
    await state.set_state(Form.atp_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход АТП", problems={})
    await message.answer(
        "🔄 Обход АТП - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото\n"
        "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
        reply_markup=get_patrol_step_keyboard()
    )

@router.message(Form.atp_patrol, F.photo)
async def handle_atp_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await process_patrol_photo(message, state, data.get('patrol_type', 'Обход АТП'))

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔄 Обход Базы 2")
async def handle_base2_patrol(message: Message, state: FSMContext):
    await state.set_state(Form.base2_patrol)
    await state.update_data(patrol_step=1, photo_paths=[], patrol_type="Обход Базы 2", problems={})
    await message.answer(
        "🔄 Обход Базы 2 - Метка 1:\n"
        "1. Нажмите «📎»\n"
        "2. Выберите «Сделать фото»\n"
        "3. Сделайте фото на метке 1\n"
        "4. Отправьте фото\n"
        "5. Если в ходе обхода обнаружена проблема - нажмите на кнопку \"❗️ Нарушение\" и опишите ее",
        reply_markup=get_patrol_step_keyboard()
    )

@router.message(Form.base2_patrol, F.photo)
async def handle_base2_patrol_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await process_patrol_photo(message, state, data.get('patrol_type', 'Обход Базы 2'))