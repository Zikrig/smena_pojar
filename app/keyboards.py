from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📹 Начало смены"))
    builder.add(types.KeyboardButton(text="🔄 Обход"))
    builder.add(types.KeyboardButton(text="🔥 Сварочные/огневые работы"))
    builder.add(types.KeyboardButton(text="⚠️ Проблема"))
    builder.add(types.KeyboardButton(text="🚨 ЧП"))
    builder.add(types.KeyboardButton(text="📞 Звонок в пожарную часть"))
    builder.adjust(2, 1, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    return builder.as_markup()

def get_fire_call_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="88137961262", callback_data="call_88137961262")
    builder.button(text="112", callback_data="call_112")
    builder.button(text="101", callback_data="call_101")
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def get_patrol_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="База 1", callback_data="patrol_base1")
    builder.button(text="АТП", callback_data="patrol_atp")
    builder.button(text="База 2", callback_data="patrol_base2")
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    builder.adjust(1, 1, 1)
    return builder.as_markup()