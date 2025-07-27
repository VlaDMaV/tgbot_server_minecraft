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


back_to_stat = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад в статистику", callback_data="server_stats")]
])


stat_menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="👤 Моя статистика", callback_data="my_stat"),
        InlineKeyboardButton(text="🥇 Топ", callback_data="top_stat")
    ],
    [
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main"),
        InlineKeyboardButton(text="⚙️ Поменять ник", callback_data="reverse_nik")
    ]
])


ower_stat_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Статистика", callback_data="server_stats")],
    [InlineKeyboardButton(text="⚙️ Поменять ник", callback_data="reverse_nik")],
    [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
])