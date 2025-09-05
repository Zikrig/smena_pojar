from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    # builder.add(types.KeyboardButton(text="📚 Инструктаж"))  # Новая кнопка
    builder.add(types.KeyboardButton(text="📹 Смена"))
    builder.add(types.KeyboardButton(text="🔄 Обход"))
    builder.add(types.KeyboardButton(text="🔥 Сварка"))
    builder.add(types.KeyboardButton(text="Сообщение для руководства"))
    builder.add(types.KeyboardButton(text="🚨 ЧП"))
    builder.add(types.KeyboardButton(text="📞 Звонок в пожарную часть"))
    builder.adjust(3, 1, 1, 1)  # Обновляем раскладку
    return builder.as_markup(resize_keyboard=True)

def get_instruction_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Обход 1", callback_data="instruction_1")
    builder.button(text="Обход 2", callback_data="instruction_2")
    builder.button(text="Обход 3", callback_data="instruction_3")
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    return builder.as_markup()

def get_fire_call_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="88137961262", callback_data="call_88137961262")
    builder.button(text="101", callback_data="call_101")
    builder.button(text="112", callback_data="call_112")
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

def get_resolved_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Решено", callback_data=f"resolve_problem")
    return builder.as_markup()


def get_patrol_step_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    builder.button(text="❗️ Нарушение", callback_data="report_problem")
    builder.adjust(2)
    return builder.as_markup()

def get_patrol_in_progress_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❗️ Нарушение", callback_data="report_problem")
    builder.button(text="✅ Завершить обход", callback_data="finish_patrol")
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    builder.adjust(1, 1, 1)
    return builder.as_markup()