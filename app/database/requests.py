import socket
import asyncio
from datetime import datetime, timedelta
from mcstatus import JavaServer

from aiogram import Bot
from app.database.models import async_session
from app.database.models import User
from sqlalchemy import func, select, update

import app.keyboards as kb
import app.text as cs
from aiogram.types import Message
from config import config

async def set_user(tg_id, name=None, username=None, is_subscribed=None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            user = User(
                tg_id=tg_id,
                name=name,
                username=username,
                is_subscribed=is_subscribed if is_subscribed is not None else False,
                subscribed_at=(datetime.utcnow() + timedelta(hours=3)) if is_subscribed else None,
                created_at=datetime.utcnow() + timedelta(hours=3)
            )
            session.add(user)
            await session.commit()
        else:
            updated = False
            if (name is not None and user.name != name):
                user.name = name
                updated = True
            if (username is not None and user.username != username):
                user.username = username
                updated = True

            if is_subscribed is not None and user.is_subscribed != is_subscribed:
                user.is_subscribed = is_subscribed
                user.subscribed_at = (datetime.utcnow() + timedelta(hours=3)) if is_subscribed else None
                updated = True

            if updated:
                await session.commit()


async def get_user(tg_id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))
    

async def subscribe_user(tg_id: int, name: str, username: str | None = None) -> User:
    """Подписать пользователя на уведомления"""
    return await set_user(
        tg_id=tg_id,
        name=name,
        username=username,
        is_subscribed=True
    )

async def unsubscribe_user(tg_id: int) -> User | None:
    """Отписать пользователя от уведомлений"""
    return await set_user(
        tg_id=tg_id, 
        is_subscribed=False
    )

async def get_subscribed_users() -> list[User]:
    """Получить всех подписанных пользователей"""
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.is_subscribed == True)
        )
        return result.scalars().all()

async def get_all_users() -> list[User]:
    """Получить всех пользователей"""
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


async def is_server_running():
    """
    Проверяет доступность Minecraft-сервера двумя способами:

    1. Проверка открытости порта

    2. Запрос статуса через протокол Minecraft
    """
    
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(config.mc_host.get_secret_value(), config.mc_port),
            timeout=3.0
        )
        writer.close()
        await writer.wait_closed()

        server = await JavaServer.async_lookup(f"{config.mc_host.get_secret_value()}:{config.mc_port}")
        status = await server.async_status()
        return True
        
    except (socket.gaierror, ConnectionRefusedError, asyncio.TimeoutError):
        return False
    except Exception as e:
        print(f"Ошибка проверки сервера: {e}")
        return False
    

async def ping_loop(bot: Bot):
    state = "up"

    while True:
        is_up = await is_server_running()

        if is_up:
            if state != "up":
                # Сервер поднялся — рассылаем уведомления подписанным
                subscribed_users = await get_subscribed_users()
                for user in subscribed_users:
                    await bot.send_message(user.tg_id, "✅ Minecraft сервер запущен!")
                state = "up"
        else:
            if state != "down":
                # Сервер упал — рассылаем уведомления подписанным
                subscribed_users = await get_subscribed_users()
                for user in subscribed_users:
                    await bot.send_message(user.tg_id, "⚠️ Minecraft сервер остановлен!")
                state = "down"

        await asyncio.sleep(60) 