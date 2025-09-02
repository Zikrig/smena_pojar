import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
from app.config import GROUP_ID
from app.database import db
import json
import logging
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GoogleSheetsLogger:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        logger.info(f"Google Sheet ID: {self.sheet_id}")
        self.credentials_path = "credentials.json"
        # Используем только scope для spreadsheets
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        self.worksheet = None
        
    async def setup_google_sheets(self):
        """Инициализация подключения к Google Sheets"""
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"Файл {self.credentials_path} не найден!")
                return False
            
            # Используем asyncio.to_thread для синхронных операций
            creds = await asyncio.to_thread(
                Credentials.from_service_account_file,
                self.credentials_path, 
                scopes=self.scopes
            )
            logger.info(f"Используем сервисный аккаунт: {creds.service_account_email}")
            
            # Авторизация также должна быть в отдельном потоке
            self.client = await asyncio.to_thread(
                gspread.authorize,
                creds
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка Google Sheets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def ensure_sheet_exists(self):
        """Убедиться, что лист доступен"""
        try:
            logger.info("Начало работы с листом")
            if not self.client:
                logger.info("Нет клиента")
                if not await self.setup_google_sheets():
                    return False
            
            # Используем альтернативный способ открытия таблицы
            # который не требует Drive API
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
            self.spreadsheet = self.client.open_by_url(spreadsheet_url)
            
            # Получаем первый лист
            self.worksheet = self.spreadsheet.get_worksheet(0)
            
            logger.info("Первый лист получен")
            
            # Проверяем, есть ли заголовки
            existing_data = await asyncio.to_thread(
                self.worksheet.get_all_values
            )
            
            if not existing_data:
                # Добавляем заголовки, если лист пустой
                headers = ["Дата", "Время", "Событие", "Автор", "Ссылка на пост"]
                await asyncio.to_thread(
                    self.worksheet.append_row,
                    headers
                )
                logger.info("Добавлены заголовки в лист")
            
            return True
                
        except Exception as e:
            logger.error(f"Ошибка при работе с листом: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def log_event(self, event_type: str, user_id: int, message_id: int = None) -> bool:
        """Логирование события в Google Sheets"""
        logger.info(f"Попытка записи события: {event_type}, user_id: {user_id}, message_id: {message_id}")
        
        # Убедимся, что лист доступен
        if not await self.ensure_sheet_exists():
            logger.error("Не удалось инициализировать Google Sheets")
            return False
            
        try:
            # Получаем информацию о пользователе из БД
            user_info = await self._get_user_info(user_id)
            username = user_info.get('username', 'Неизвестно')
            full_name = user_info.get('full_name', 'Неизвестно')
            logger.info(f"Информация о пользователе получена: {full_name} (@{username})")
            
            # Формируем ссылку на сообщение
            message_link = await self._get_message_link(message_id) if message_id else 'Нет ссылки'
            logger.info(f"Ссылка на сообщение: {message_link}")
            
            # Получаем текущее время
            now = datetime.now()
            date_str = now.strftime("%d.%m.%Y")
            time_str = now.strftime("%H:%M:%S")
            
            # Добавляем запись в таблицу
            row = [date_str, time_str, event_type, f"{full_name} (@{username})", message_link]
            logger.info(f"Добавляем строку: {row}")
            
            # Используем asyncio.to_thread для синхронной операции
            await asyncio.to_thread(
                self.worksheet.append_row, 
                row
            )
            
            logger.info(f"Запись добавлена в Google Sheets: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи в Google Sheets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def _get_user_info(self, user_id: int) -> Dict[str, Any]:
        """Получение информации о пользователе из БД"""
        try:
            logger.info(f"Получаем информацию о пользователе {user_id} из БД")
            
            if not hasattr(db, 'pool') or not db.pool:
                logger.error("Путь к БД не инициализирован")
                return {}
                
            async with db.pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT username, full_name FROM users WHERE user_id = $1',
                    user_id
                )
                result = dict(user) if user else {}
                logger.info(f"Результат запроса к БД: {result}")
                return result
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return {}

    async def _get_message_link(self, message_id: int) -> str:
        """Формирование ссылки на сообщение в группе"""
        try:
            logger.info(f"Формируем ссылку для message_id: {message_id}, GROUP_ID: {GROUP_ID}")
            
            if not GROUP_ID:
                logger.error("GROUP_ID не установлен")
                return "GROUP_ID не установлен"
                
            # Для групп без username формируем ссылку через ID
            chat_id = str(GROUP_ID).replace('-100', '')
            link = f"https://t.me/c/{chat_id}/{message_id}"
            logger.info(f"Сформирована ссылка: {link}")
            return link
        except Exception as e:
            logger.error(f"Ошибка формирования ссылки: {e}")
            return "Ошибка формирования ссылки"

# Глобальный экземпляр логгера
gs_logger = GoogleSheetsLogger()