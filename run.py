import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import config
from app.handlers import router
from app.database.models import init_db
from app.utils.server_task import ServerTasks
from app.database.requests import ping_loop


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()


async def main():
    await init_db()
    dp.include_router(router)

    tasks = [
        asyncio.create_task(ping_loop(bot)),
        asyncio.create_task(ServerTasks(bot).manage_tasks())
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