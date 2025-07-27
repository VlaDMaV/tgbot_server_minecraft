from mcrcon import MCRcon
import asyncio

class RconClient:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.mcr = None

    def connect(self):
        self.mcr = MCRcon(self.host, self.password, port=self.port)
        self.mcr.connect()

    def disconnect(self):
        if self.mcr:
            self.mcr.disconnect()

    def run_command(self, command):
        return self.mcr.command(command)

    async def run_command_async(self, command):
        return await asyncio.to_thread(self.run_command, command)