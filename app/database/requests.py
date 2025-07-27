import re
import socket
import asyncio
import logging
import paramiko
from datetime import datetime, timedelta
from mcstatus import JavaServer
from mcrcon import MCRcon

from aiogram import Bot
from app.database.models import async_session
from app.database.models import User
from sqlalchemy import func, select, update

import app.keyboards as kb
import app.text as cs
from aiogram.types import Message
from config import config
from app.utils.rcon_utils import RconClient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]
)

bot = Bot(token=config.bot_token.get_secret_value())


async def set_user(tg_id, name=None, username=None, is_subscribed=True):
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
    Проверяет доступность Minecraft-сервера через протокол Minecraft.
    """
    
    try:
        server = await JavaServer.async_lookup(f"{config.mc_host.get_secret_value()}:{config.mc_port}")
        status = await asyncio.wait_for(server.async_status(), timeout=2.0)
        return True
        
    except (socket.gaierror, ConnectionRefusedError, asyncio.TimeoutError):
        return False
    except Exception as e:
        print(f"Ошибка проверки сервера: {e}")
        return False
    

async def ping_loop(bot: Bot):
    state = "up"
    failure_count = 0
    success_count = 0

    while True:
        is_up = await is_server_running()

        if is_up:
            success_count += 1
            failure_count = 0
        else:
            failure_count += 1
            success_count = 0

        if is_up:
            if success_count >= 3 and state != "up":
                # Сервер поднялся — рассылаем уведомления подписанным
                subscribed_users = await get_subscribed_users()
                for user in subscribed_users:
                    await bot.send_message(user.tg_id, "✅ Minecraft сервер запущен!")
                state = "up"
        else:
            if failure_count >= 3 and state != "down":
                # Сервер упал — рассылаем уведомления подписанным
                subscribed_users = await get_subscribed_users()
                for user in subscribed_users:
                    await bot.send_message(user.tg_id, "⚠️ Minecraft сервер остановлен!")
                state = "down"

        await asyncio.sleep(10) 


async def periodic_save_task():
    while True:
        await asyncio.sleep(300) 
        result = run_rcon_command("save-all")
        logging.info(f"[save-all] Команда выполнена: {result}")


def get_server_stats(host: str, port: int, password: str) -> str:
    """
    Возвращает строку с текущей статистикой сервера Minecraft по RCON.
    """
    try:
        with MCRcon(host, password, port=port) as mcr:
            # Получаем список игроков
            list_resp = mcr.command("list")

            # Пробуем получить TPS (если поддерживается)
            try:
                tps_resp = mcr.command("tps")
            except Exception:
                tps_resp = "TPS недоступен."

            # Собираем всё
            stats_text = (
                "📊 Статистика сервера:\n\n"
                f"👥 Онлайн:\n{list_resp}\n\n"
                f"⚙️ TPS:\n{tps_resp}\n"
            )

            return stats_text
    except Exception as e:
        return f"❌ Не удалось получить статистику:\n{e}"
    

def run_rcon_command(command: str, host=config.mc_host.get_secret_value(), port=config.rcon_port, password=config.rcon_pass.get_secret_value()):
    try:
        with MCRcon(host, password, port=port) as mcr:
            return mcr.command(command)
    except Exception as e:
        return f"Ошибка RCON: {e}"
    

async def run_rcon_command2(command: str):
    try:
        client = RconClient(
            host=config.mc_host.get_secret_value(),
            port=config.rcon_port,
            password=config.rcon_pass.get_secret_value()
        )
        client.connect()
        result = await client.run_command_async(command)
        client.disconnect()
        return result
    except Exception as e:
        return f"Ошибка RCON: {e}"
    

def run_ssh_command(
    command: str,
    host=config.mc_host.get_secret_value(),
    port=config.ssh_port,
    user=config.ssh_user.get_secret_value(),
    password=config.ssh_pass.get_secret_value()
):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=host, port=port, username=user, password=password)

        stdin, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode()
        err = stderr.read().decode()

        client.close()

        if err:
            return f"❌ Ошибка при выполнении команды:\n{err.strip()}"
        return out.strip() if out.strip() else "✅ Команда выполнена, но вывода нет."

    except Exception as e:
        return f"❌ SSH-подключение не удалось: {e}"
    

async def get_last_death_location(mc_name: str) -> str | None:
    command=f"/data get entity {mc_name} LastDeathLocation"
    response = await run_rcon_command2(command)
    match = re.search(r"pos: \[I; (-?\d+), (-?\d+), (-?\d+)\]", response)
    if match:
        x, y, z = match.groups()
        return f"X={x}, Y={y}, Z={z}"
    return None
    

async def get_telegram_id_by_mc_name(mc_name: str) -> int | None:
    async with async_session() as session:
        stmt = select(User).where(User.mc_name == mc_name)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return user.tg_id
        return None
    

async def notify_player_death(mc_name: str, death_reason: str):
    tg_id = await get_telegram_id_by_mc_name(mc_name)
    if not tg_id:
        await bot.send_message(config.admin_id, f"💀 Игрок {mc_name} умер, Telegram ID не найден.")
        return
    
    coords = await get_last_death_location(mc_name)
    
    text = f"💀 Ты ({mc_name}) умер на сервере!\nПричина: {death_reason}"
    if coords:
        text += f"\nКоординаты смерти: {coords}"
    
    await bot.send_message(tg_id, text)

    admin_text = f"💀 Умер {mc_name}."
    if coords:
        admin_text += f" Координаты: {coords}"
    await bot.send_message(config.admin_id, admin_text)


async def process_log_line(line: str):

    match = re.search(r'\]: ([^\s]+) joined the game', line)
    if match:
        player = match.group(1)
        logging.info(f"🟢 Игрок {player} подключился к серверу!")
        await bot.send_message(config.admin_id, f"🟢 Игрок {player} подключился к серверу!")

    match_leave = re.search(r'\]: ([^\s]+) left the game', line)
    if match_leave:
        player = match_leave.group(1)
        logging.info(f"🔴 Игрок {player} вышел с сервера!")
        await bot.send_message(config.admin_id, f"🔴 Игрок {player} вышел с сервера!")
        return
    
    match_chat_alt = re.search(r'\[Not Secure\] <([^>]+)> (.+)', line)
    if match_chat_alt:
        player = match_chat_alt.group(1)
        message = match_chat_alt.group(2)
        logging.info(f"💬 {player}: {message}")
        await bot.send_message(config.admin_id, f"💬 {player}: {message}")
        return
    
    match_chat = re.search(r'\]: ([^\s]+): (.+)', line)
    if match_chat:
        player = match_chat.group(1)
        message = match_chat.group(2)
        logging.info(f"💬 {player}: {message}")
        await bot.send_message(config.admin_id, f"💬 {player}: {message}")
        return
    
    for pattern in cs.death_patterns:
        if pattern in line:
            player_match = re.search(r'\]: \[\d{2}:\d{2}:\d{2} INFO\]: (\S+)', line)
            player = player_match.group(1) if player_match else "Игрок"

            if player is None:
                logging.warning("Не смогли распарсить ник умершего игрока из лога.")
                return

            logging.info(f"💀 Игрок {player} умер! Причина: {pattern}")

            await notify_player_death(player, pattern)

            return
    

def ssh_log_reader(host, port, user, password, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=user, password=password)

        stdin, stdout, stderr = client.exec_command("journalctl -u minecraft -f")

        for line in iter(stdout.readline, ""):
            if line:
                # Отправляем строку в asyncio очередь из другого потока
                asyncio.run_coroutine_threadsafe(queue.put(line.strip()), loop)

    except Exception as e:
        logging.error(f"SSH error: {e}")
        asyncio.run_coroutine_threadsafe(queue.put(f"❌ SSH error: {e}"), loop)
    finally:
        if client:
            try:
                client.close()
            except Exception:
                pass
    

async def log_watcher_task(host, port, user, password):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    # Запускаем ssh_log_reader в отдельном потоке
    loop.run_in_executor(None, ssh_log_reader, host, port, user, password, queue, loop)

    try:
        while True:
            line = await queue.get()
            await process_log_line(line)
    except asyncio.CancelledError:
        logging.info("Log watcher task cancelled")
        raise


async def update_mc_name(tg_id: int, mc_name: str):
    async with async_session() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(mc_name=mc_name)
        await session.execute(stmt)
        await session.commit()


async def get_scoreboard_stat(mc_name: str, objective: str) -> int | str:
    command = f"scoreboard players get {mc_name} {objective}"
    output = await run_rcon_command2(command)

    print(f"RCON ответ: {output}")

    if "Can't get value" in output or "none is set" in output:
        return "Пока нет данных"

    match = re.search(r"has (\d+)", output)
    if match:
        return int(match.group(1))
    return "Неизвестный формат ответа"


async def get_player_stats(mc_name: str) -> str:
    stats_lines = [f"Статистика игрока <b>{mc_name}</b>:"]

    for obj in cs.OBJECTIVES:
        ru_name = cs.OBJECTIVES_RU.get(obj.lower(), obj) 
        val = await get_scoreboard_stat(mc_name, obj)

        if obj == "walk_km" and isinstance(val, int):
            val = f"{val / 1000:.2f}"

        stats_lines.append(f"• {ru_name}: {val}")

    return "\n".join(stats_lines)