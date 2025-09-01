from app.database import db
from app.config import EXCLUDED_USERS

async def send_patrol_reminders(bot, patrol_type, excluded_users):
    users = await db.get_all_users()
    
    for user in users:
        user_id = user['user_id']
        
        # Пропускаем исключенных пользователей
        if user_id in excluded_users:
            continue
            
        if patrol_type == "base1":
            message = "⏰ Напоминание: 8:15 - Сделайте обход базы-1"
        elif patrol_type == "all":
            message = "⏰ Напоминание: 13:00 - Сделайте обходы АТП и базы-2"
        else:
            return
            
        try:
            await bot.send_message(user_id, message)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")