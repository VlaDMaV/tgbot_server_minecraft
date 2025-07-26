import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import config
from app.handlers import router
from app.database.models import init_db

from app.database.requests import ping_loop

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()

async def main():
    await init_db()
    dp.include_router(router)

    asyncio.create_task(ping_loop(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен")