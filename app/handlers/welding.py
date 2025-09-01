
from aiogram import Router, F
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo, FSInputFile
from aiogram.enums import ChatType, ParseMode
from aiogram.fsm.context import FSMContext
import os

from app.states import Form
from app.keyboards import get_cancel_keyboard, get_main_keyboard
from app.config import GROUP_ID
from app.utils import get_moscow_time
from app.image_processor import ImageProcessor


router = Router()

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "🔥 Сварочные/огневые работы")
async def handle_welding_work(message: Message, state: FSMContext):
    await state.set_state(Form.welding_work)
    await message.answer(
        "🔥 Сварочные/огневые работы:\n"
        "Введите данные в формате:\n"
        "<b>Место работы / ответственные / вид работ</b>\n\n"
        "Пример: <code>Цех 1 / Савельев, Тарасов / сварка металлоконструкций</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )

@router.message(Form.welding_work, F.text)
async def handle_welding_work_data(message: Message, state: FSMContext):
    await state.update_data(welding_info=message.text)
    await message.answer("📸 Теперь отправьте фото/видео начала работ:", reply_markup=get_cancel_keyboard())

@router.message(Form.welding_work, F.photo | F.video)
async def handle_welding_work_media(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        welding_info = data.get("welding_info")
        if not welding_info:
            await message.answer("❌ Сначала введите информацию о работах!", reply_markup=get_cancel_keyboard())
            return

        current_time = get_moscow_time().strftime("%Y-%m-%d %H:%M:%S")

        if message.photo:
            # Скачиваем фото
            file_id = message.photo[-1].file_id
            file = await message.bot.get_file(file_id)
            input_path = f"app/data/temp_{file_id}.jpg"
            await message.bot.download_file(file.file_path, destination=input_path)

            # Накладываем время
            output_path = f"app/data/output_{file_id}.jpg"
            ImageProcessor.add_text_with_outline(input_path, output_path, current_time)

            media_item = {"type": "photo", "path": output_path}
            os.remove(input_path)  # удаляем исходник
        elif message.video:
            # Для видео только сохраняем (время в текст подписи)
            file_id = message.video.file_id
            file = await message.bot.get_file(file_id)
            output_path = f"app/data/output_{file_id}.mp4"
            await message.bot.download_file(file.file_path, destination=output_path)
            media_item = {"type": "video", "path": output_path}
        else:
            await message.answer("❌ Отправьте фото или видео.", reply_markup=get_cancel_keyboard())
            return

        # Если это первое медиа — сохраняем и ждём второе
        if "start_media" not in data:
            await state.update_data(start_media=media_item)
            await message.answer("✅ Фото/видео начала работ принято. Теперь отправьте фото/видео окончания работ:", reply_markup=get_cancel_keyboard())
            return

        # Второе медиа — собираем альбом
        start = data["start_media"]
        caption = (
            f"🔥 <b>Сварочные/огневые работы</b>\n"
            f"⏰ Время: {current_time}\n"
            f"📝 Информация: {welding_info}"
        )

        media = []
        # первый элемент — с подписью
        if start["type"] == "photo":
            media.append(InputMediaPhoto(media=FSInputFile(start["path"]), caption=caption, parse_mode=ParseMode.HTML))
        else:
            media.append(InputMediaVideo(media=FSInputFile(start["path"]), caption=caption, parse_mode=ParseMode.HTML))

        # второй элемент — без подписи
        if media_item["type"] == "photo":
            media.append(InputMediaPhoto(media=FSInputFile(media_item["path"])))
        else:
            media.append(InputMediaVideo(media=FSInputFile(media_item["path"])))

        await message.bot.send_media_group(chat_id=GROUP_ID, media=media)

        # Чистим временные файлы
        for m in [start, media_item]:
            try:
                os.remove(m["path"])
            except FileNotFoundError:
                pass

        await state.clear()
        await message.answer("✅ Все данные по сварочным работам отправлены в группу!", reply_markup=get_main_keyboard())

    except Exception:
        await message.answer("❌ Произошла ошибка при обработке данных!", reply_markup=get_main_keyboard())