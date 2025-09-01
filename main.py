from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType 
from aiogram.fsm.context import FSMContext
from aiogram import F



from app.keyboards import get_main_keyboard
from app.config import BOT_TOKEN, EXCLUDED_USERS
from app.database import db
from app.scheduler import send_patrol_reminders

# Импорты обработчиков
from app.handlers.start import router as start_router
from app.handlers.shift_start import router as shift_start_router
from app.handlers.patrols import router as patrols_router
from app.handlers.problems import router as problems_router
from app.handlers.welding import router as welding_router
from app.handlers.emergency import router as emergency_router
from app.handlers.fire_call import router as fire_call_router
# from app.handlers.instruction import router as instruction_router

# Создаем папку для временных файлов
Path("app/data").mkdir(exist_ok=True)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Подключаем все роутеры
dp.include_router(start_router)
dp.include_router(shift_start_router)
dp.include_router(patrols_router)
dp.include_router(problems_router)
dp.include_router(welding_router)
dp.include_router(emergency_router)
dp.include_router(fire_call_router)
# dp.include_router(instruction_router)

# Функция для запуска планировщика
async def start_scheduler():
    # Рассылка в 8:15 - обход базы 1
    scheduler.add_job(
        send_patrol_reminders,
        CronTrigger(hour=8, minute=15),
        args=[bot, "base1", EXCLUDED_USERS]
    )
    
    # Рассылка в 13:00 - обходы АТП и базы 2
    scheduler.add_job(
        send_patrol_reminders,
        CronTrigger(hour=13, minute=00),
        args=[bot, "all", EXCLUDED_USERS]
    )
    
    scheduler.start()

# Запуск бота
if __name__ == "__main__":
    import asyncio
    from aiogram.filters import Command
    
    @dp.message(F.chat.type == ChatType.PRIVATE, CommandStart())
    async def cmd_start(message: Message,  state: FSMContext):
        # Регистрация пользователя
        await db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name
        )
        await state.clear()
        await message.answer(
            "Добро пожаловать! Выберите действие:",
            reply_markup=get_main_keyboard()
        )
    
    async def main():
        # Инициализация БД
        await db.create_pool()
        await db.create_tables()
        
        # Запуск планировщика
        await start_scheduler()
        
        # Запуск бота
        await dp.start_polling(bot)
    
    asyncio.run(main())