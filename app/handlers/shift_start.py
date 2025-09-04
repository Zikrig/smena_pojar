from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType 
from datetime import datetime
from aiogram.enums import ParseMode

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.google_sheets import gs_logger


router = Router()

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "📹 Смена")
async def handle_shift_start(message: Message, state: FSMContext):
    await state.set_state(Form.shift_start)
    await message.answer(
        text='''📹 Для начала смены:
        1. Записываем видео сообщение - «Кружок». Кнопка начала записи кружка находится справа снизу. Если вы видите там значок диктофона – переключите на камеру нажав на него КОРОТКО.
        3. Зажмите кнопку (кружок в квадрате) и записывайте видеокружок.
        4. Глядя в камеру сообщите ФИО, дату и время начала смены.
        5. Отпустите кнопку – сообщение отправится автоматически.''',
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.shift_start, F.video_note)
async def handle_shift_start_video_note(message: Message, state: FSMContext):
    current_time = get_moscow_time().strftime("%H:%M")
    current_date = get_moscow_time().strftime("%d.%m.%Y")
    
    # Сначала отправляем описание в группу
    caption = (
        f"📹 <b>Начало смены</b>\n"
        f"⏰ Время: {current_time}\n"
        f"📅 Дата: {current_date}\n"
        f"🧍 Видеокружок с сотрудником:"
    )
    
    await message.bot.send_message(
        chat_id=GROUP_ID,
        text=caption,
        parse_mode=ParseMode.HTML
    )
    
    # Затем отправляем сам видеокружок
    sent_message = await message.bot.send_video_note(
        chat_id=GROUP_ID,
        video_note=message.video_note.file_id
    )
    
    await gs_logger.log_event(  # Добавляем логирование
        "Начало смены",
        message.from_user.id,
        sent_message.message_id
    )
    
    await state.clear()
    await message.answer("✅ Видеокружок начала смены отправлен в группу!", reply_markup=get_main_keyboard())

@router.message(Form.shift_start, F.video)
async def handle_wrong_video_format(message: Message):
    await message.answer(
        '''❌ Пожалуйста, отправьте именно <b>видеокружок</b>, а не обычное видео!
        📹 Для начала смены:
        1. Записываем видео сообщение - «Кружок». Кнопка начала записи кружка находится справа снизу. Если вы видите там значок диктофона – переключите на камеру нажав на него КОРОТКО.
        3. Зажмите кнопку (кружок в квадрате) и записывайте видеокружок.
        4. Глядя в камеру сообщите ФИО, дату и время начала смены.
        5. Отпустите кнопку – сообщение отправится автоматически.''',
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.shift_start)
async def handle_other_messages(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте видеокружок для начала смены\n"
        "Если хотите прервать процесс, нажмите «Отмена»",
        reply_markup=get_cancel_keyboard()
    )