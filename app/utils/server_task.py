import asyncio
import logging

from config import config
from app.database.requests import is_server_running, run_rcon_command, ssh_log_reader, process_log_line


logging.basicConfig(level=logging.INFO)


class ServerTasks:
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.server_was_up = False
        self.config = config


    async def manage_tasks(self):
        while True:
            is_up = await is_server_running()

            if is_up and not self.server_was_up:
                await self.start_tasks()
                self.server_was_up = True
                logging.info("Сервер запущен, задачи запущены.")
            elif not is_up and self.server_was_up:
                await self.stop_tasks()
                self.server_was_up = False
                logging.info("Сервер остановлен, задачи остановлены.")

            await asyncio.sleep(10)

    
    async def start_tasks(self):
        """Запуск всех задач, связанных с сервером"""
        if 'save_task' not in self.tasks:
            self.tasks['save_task'] = asyncio.create_task(self.safe_periodic_save_task())
        
        if 'log_watcher' not in self.tasks:
            self.tasks['log_watcher'] = asyncio.create_task(
                self.safe_log_watcher_task(
                    host=self.config.mc_host.get_secret_value(),
                    port=self.config.ssh_port,
                    user=self.config.ssh_user.get_secret_value(),
                    password=self.config.ssh_pass.get_secret_value()
                )
            )

    
    async def stop_tasks(self):
        """Остановка всех задач, связанных с сервером"""
        for name, task in list(self.tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.tasks[name]


    async def safe_periodic_save_task(self):
        """Защищенная версия задачи сохранения"""
        try:
            while True:
                if await is_server_running():
                    try:
                        result = run_rcon_command("save-all")
                        logging.info(f"[save-all] Команда выполнена: {result}")
                    except Exception as e:
                        logging.error(f"[save-all] Ошибка: {e}")
                await asyncio.sleep(300)
        except asyncio.CancelledError:
            logging.info("Periodic save task cancelled")
            raise


    async def safe_log_watcher_task(self, host, port, user, password):
        """Защищенная версия задачи мониторинга логов"""
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        try:
            while True:
                if await is_server_running():
                    if not hasattr(self, '_ssh_reader_running'):
                        loop.run_in_executor(
                            None, 
                            ssh_log_reader, 
                            host, port, user, password, queue, loop
                        )
                        self._ssh_reader_running = True

                    try:
                        line = await asyncio.wait_for(queue.get(), timeout=1.0)
                        await process_log_line(line)
                    except asyncio.TimeoutError:
                        continue
                else:
                    if hasattr(self, '_ssh_reader_running'):
                        del self._ssh_reader_running
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            logging.info("Log watcher task cancelled")
            raise