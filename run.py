import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import config
from app.handlers import router
from app.database.models import init_db

from app.database.requests import periodic_save_task, ping_loop, log_watcher_task

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()

async def main():
    await init_db()
    dp.include_router(router)

    tasks = [
        asyncio.create_task(ping_loop(bot)),
        asyncio.create_task(periodic_save_task()),
        asyncio.create_task(log_watcher_task(
            host=config.mc_host.get_secret_value(),
            port=config.ssh_port,
            user=config.ssh_user.get_secret_value(),
            password=config.ssh_pass.get_secret_value()
        ))
    ]

    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logging.info("Polling cancelled.")
    finally:
        logging.info("Отмена всех фоновых задач...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logging.info("Все фоновые задачи остановлены.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен")