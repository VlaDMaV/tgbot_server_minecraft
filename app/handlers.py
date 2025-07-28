from math import ceil
import asyncio

import logging
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import config
import app.keyboards as kb
import app.database.requests as rq
import app.text as cs


logging.basicConfig(level=logging.INFO)
router = Router()

class MCNameState(StatesGroup):
    waiting_for_mc_name = State()


# Хэндлер на команду /start
@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    existing_user = await rq.get_user(user.id)

    if not existing_user:
        await rq.set_user(user.id, user.full_name, user.username, is_subscribed=True)
    await message.answer(
        text=cs.welcome_text, 
        parse_mode="HTML",
        reply_markup=kb.main_menu
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        text=cs.welcome_text, 
        parse_mode="HTML",
        reply_markup=kb.main_menu)


@router.callback_query(F.data == "server_status")
async def show_status(callback: CallbackQuery):
    online = await rq.is_server_running()
    status = "🟢 Сервер работает!" if online else "🔴 Сервер не работает"
    await callback.answer(status)


@router.callback_query(F.data == "server_control")
async def show_settings(callback: CallbackQuery):
    user = callback.from_user
    existing_user = await rq.get_user(user.id)

    if not existing_user:
        await rq.set_user(user.id, user.full_name, user.username, is_subscribed=True) 
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
async def server_stats(callback: CallbackQuery):
    await callback.message.edit_text("⏳ Загружаю статистику сервера...")

    is_up = await rq.is_server_running()

    if is_up:
        stats = rq.get_server_stats(host=config.mc_host.get_secret_value(), port=config.rcon_port, password=config.rcon_pass.get_secret_value())

        await callback.message.edit_text(
            text=stats,
            reply_markup=kb.stat_menu
        )
    else:
        await callback.message.edit_text(text=cs.none_text, parse_mode="HTML",reply_markup=kb.back_to_main)


@router.callback_query(F.data == "my_stat")
async def handle_my_stat(callback: CallbackQuery, state: FSMContext):
    user = await rq.get_user(callback.from_user.id)

    if not user:
        await rq.set_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
        user = await rq.get_user(callback.from_user.id)

    if not user.mc_name:
        await callback.message.edit_text("❗ У тебя не указан ник Minecraft.\n\nВведи его сейчас:")
        await state.set_state(MCNameState.waiting_for_mc_name)
    else:
        await callback.message.edit_text("⏳ Загружаю вашу статистику...")

        is_up = await rq.is_server_running()

        if is_up:
            stats = await rq.get_player_stats(user.mc_name)
            await callback.message.edit_text(f"📊 Статистика игрока <b>{user.mc_name}</b>:\n\n{stats}", parse_mode="HTML",reply_markup=kb.ower_stat_menu)
        else:
            await callback.message.edit_text(text=cs.none_text, parse_mode="HTML",reply_markup=kb.back_to_main)


@router.callback_query(F.data == "reverse_nik")
async def reverse_nik(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user
    existing_user = await rq.get_user(user.id)

    if not existing_user:
        await rq.set_user(user.id, user.full_name, user.username, is_subscribed=True) 
        existing_user = await rq.get_user(user.id)

    await callback.message.edit_text("❗ Введи новый ник:",reply_markup=kb.back_to_main)
    await state.set_state(MCNameState.waiting_for_mc_name)

    
@router.message(MCNameState.waiting_for_mc_name)
async def process_mc_name_input(message: Message, state: FSMContext):
    mc_name = message.text.strip()

    await rq.update_mc_name(message.from_user.id, mc_name)
    await state.clear()

    await message.answer(f"✅ Ник <b>{mc_name}</b> сохранён!\n\nТеперь ты можешь снова нажать «🥇 Моя статистика»", parse_mode="HTML",reply_markup=kb.stat_menu)


@router.callback_query(F.data == "help")
async def help(callback: CallbackQuery):
    await callback.message.edit_text(
        text=cs.help_text, parse_mode="HTML",
        reply_markup=kb.back_to_main)


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        text=cs.about_text, parse_mode="HTML",
        reply_markup=kb.back_to_main)
    

@router.callback_query(F.data == "top_stat")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        text=cs.top_text, parse_mode="HTML",
        reply_markup=kb.back_to_stat)


@router.message()
async def any_message_handler(message: Message):
    await message.answer("Пожалуйста, нажмите /start")