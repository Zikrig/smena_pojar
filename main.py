
from pathlib import Path
from aiogram import Bot, Dispatcher


from app.config import BOT_TOKEN

# Импортируем и подключаем обработчики после инициализации bot и dp
from app.handlers.start import router as start_router
from app.handlers.shift_start import router as shift_start_router
from app.handlers.patrols import router as patrols_router
from app.handlers.problems import router as problems_router
from app.handlers.welding import router as welding_router
from app.handlers.emergency import router as emergency_router
from app.handlers.fire_call import router as fire_call_router


# Создаем папку для временных файлов
Path("app/data").mkdir(exist_ok=True)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Подключаем все роутеры
dp.include_router(start_router)
dp.include_router(shift_start_router)
dp.include_router(patrols_router)
dp.include_router(problems_router)
dp.include_router(welding_router)
dp.include_router(emergency_router)
dp.include_router(fire_call_router)

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)