import discord
from discord.ext import commands
from utils.patreon import SubscriptionUser


class Premium(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    # /premium command removed per request


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Premium(client))
