import os
import aiohttp
import discord
from discord.ext import commands, tasks


class KeepAwake(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.pinger.start()

    @tasks.loop(minutes=12)
    async def pinger(self):
        await self.client.wait_until_ready()
        url = os.getenv("RENDER_EXTERNAL_URL")
        if not url:
            host = os.getenv("API_HOST", "127.0.0.1")
            port = os.getenv("API_PORT", "8000")
            url = f"http://{host}:{port}/status"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    await resp.read()
        except Exception:
            pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(KeepAwake(client))
