from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.enums import ChatType
import os
import logging

from app.keyboards import get_main_keyboard, get_instruction_keyboard

router = Router()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

logger.info("Инструкция: Инициализация обработчика")

# Описания для инструктажей
INSTRUCTIONS = {
    "instruction_1": {
        "image": "/data/obhod1.jpg",
        "document": "/data/instr1.docx",
        "text": "📋 Схема обхода 1: Основные точки контроля на территории"
    },
    "instruction_2": {
        "image": "/data/obhod1.jpg", 
        "document": "/data/instr1.docx",
        "text": "📋 Схема обхода 2: Внутренние помещения и объекты"
    },
    "instruction_3": {
        "image": "/data/obhod3.jpg",
        "document": "/data/instr3.docx", 
        "text": "📋 Схема обхода 3: Периметр и внешние зоны"
    }
}

@router.message(F.chat.type == ChatType.PRIVATE, F.text == "📚 Инструктаж")
async def handle_instruction(message: Message):
    await message.answer(
        "📚 Выберите схему обхода:",
        reply_markup=get_instruction_keyboard()
    )

@router.callback_query(F.data.startswith("instruction_"))
async def handle_instruction_select(callback: CallbackQuery):
    instruction_type = callback.data
    instruction = INSTRUCTIONS.get(instruction_type)
    
    if instruction:
        try:
            image_path = instruction["image"]
            doc_path = instruction["document"]
            
            # Логируем пути для отладки
            logger.info(f"Проверяем существование файлов:")
            logger.info(f"Изображение: {image_path}")
            logger.info(f"Документ: {doc_path}")
            logger.info(f"Текущая рабочая директория: {os.getcwd()}")
            logger.info(f"Содержимое /data: {os.listdir('/data') if os.path.exists('/data') else 'Папка не существует'}")
            
            # Проверяем существование файлов
            if not os.path.exists(image_path):
                error_msg = f"❌ Изображение не найдено по пути: {image_path}"
                logger.error(error_msg)
                await callback.message.answer(error_msg)
                return
                
            if not os.path.exists(doc_path):
                error_msg = f"❌ Документ не найден по пути: {doc_path}"
                logger.error(error_msg)
                await callback.message.answer(error_msg)
                return
            
            # Логируем успешное нахождение файлов
            logger.info(f"Файлы найдены, начинаем отправку")
            
            # Отправляем изображение
            photo = FSInputFile(image_path)
            await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=photo,
                caption=instruction["text"]
            )
            
            # Отправляем документ
            document = FSInputFile(doc_path)
            await callback.bot.send_document(
                chat_id=callback.from_user.id,
                document=document,
                caption="📄 Инструкция по обходу"
            )
            
            logger.info(f"Инструкция {instruction_type} успешно отправлена пользователю {callback.from_user.id}")
            
        except Exception as e:
            error_msg = f"❌ Ошибка при отправке инструкции: {e}"
            logger.error(error_msg, exc_info=True)
            await callback.message.answer(error_msg)
    else:
        await callback.message.answer("❌ Инструкция не найдена")
    
    await callback.answer()