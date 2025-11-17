import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime


import aiohttp
from utils.emojis import *


class Utility(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        client.launch_time = datetime.now()
        self.client.help_command = None

    # /support command removed per branding and command cleanup

    pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utility(client))
