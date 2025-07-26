from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='🟢 Статус', callback_data='server_status'),
        InlineKeyboardButton(text='📊 Статистика', callback_data='server_stats')
    ],
    [
        InlineKeyboardButton(text='⚙️ Настройки', callback_data='server_control'),
        InlineKeyboardButton(text='📌 О нас', callback_data='about')
    ],
    [InlineKeyboardButton(text='❓ Помощь', callback_data='help')]
])


back_to_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
])