from math import ceil

import logging
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
import app.keyboards as kb
import app.database.requests as rq
import app.text as cs

logging.basicConfig(level=logging.INFO)
router = Router()


# Хэндлер на команду /start
@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    existing_user = await rq.get_user(user.id)

    if not existing_user:
        await rq.set_user(user.id, user.full_name, user.username)
    await message.answer(
        text=f"🎮 Добро пожаловать в Vinecraft Bot!\n\n"
        
            "Подключайтесь: vinecraft.vladmav.netcraze.pro\n\n"
            
            "Выберите действие:",
        reply_markup=kb.main_menu
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        text=f"🎮 Добро пожаловать в Vinecraft Bot!\n\n"
            
             "Выберите действие:",
            reply_markup=kb.main_menu)


@router.callback_query(F.data == "server_status")
async def show_status(callback: CallbackQuery):
    online = await rq.is_server_running()
    status = "🟢 Сервер работает!" if online else "🔴 Сервер не работает"
    await callback.answer(status)


@router.callback_query(F.data == "server_control")
async def snow_settings(callback: CallbackQuery):
    user = callback.from_user
    existing_user = await rq.get_user(user.id)

    text = (
        "🔔 <b>Управление уведомлениями сервера</b>\n\n"
        f"Текущий статус: {'✅ Подписаны' if existing_user and existing_user.is_subscribed else '❌ Не подписаны'}\n\n"
        "Получать уведомления при:\n"
        "• Запуске/остановке сервера\n"
        "• Изменении статуса\n"
        "• Важных событиях"
    )

    builder = InlineKeyboardBuilder()
    if user and existing_user.is_subscribed:
        builder.button(text="🔕 Отписаться", callback_data="unsubscribe_notifications")
    else:
        builder.button(text="🔔 Подписаться", callback_data="subscribe_notifications")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "subscribe_notifications")
async def subscribe(callback: CallbackQuery):
    user = callback.from_user
    await rq.subscribe_user(user.id, user.full_name, user.username)

    text = (
        "🔔 Вы успешно подписались на уведомления.\n\n"
        "Хотите отписаться?"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🔕 Отписаться", callback_data="unsubscribe_notifications")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    
    await callback.answer()


@router.callback_query(F.data == "unsubscribe_notifications")
async def unsubscribe(callback: CallbackQuery):
    await rq.unsubscribe_user(callback.from_user.id)
    
    # Меняем текст сообщения и кнопки сразу после нажатия
    text = (
        "🔕 Вы успешно отписались от уведомлений.\n\n"
        "Хотите снова подписаться?"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Подписаться", callback_data="subscribe_notifications")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    
    await callback.answer() 


@router.callback_query(F.data == "server_stats")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        text=cs.stat_text, parse_mode="HTML",
        reply_markup=kb.back_to_main)


@router.callback_query(F.data == "help")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        text=cs.help_text, parse_mode="HTML",
        reply_markup=kb.back_to_main)


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        text=cs.about_text, parse_mode="HTML",
        reply_markup=kb.back_to_main)