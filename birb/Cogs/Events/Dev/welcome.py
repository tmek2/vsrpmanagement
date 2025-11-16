import discord
from discord.ext import commands
from utils.emojis import *
import os
import re


class welcome(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "1370845563230355537"))
        self.AUTO_ROLE_1_ID = int(os.getenv("AUTO_ROLE_1_ID", "1370840224267239484"))
        self.AUTO_ROLE_2_ID = int(os.getenv("AUTO_ROLE_2_ID", "1370841279801458698"))
        self.COUNTER_EMOJI_SPEC = os.getenv("COUNTER_EMOJI_SPEC", "<:humans:1439706773505183804>")
        self.LINK_EMOJI_SPEC = os.getenv("LINK_EMOJI_SPEC", "<:lightbulb:1439706775270985808>")
        self.LINK_LABEL = os.getenv("LINK_LABEL", "Information")
        self.LINK_URL = os.getenv("LINK_URL", "https://discord.com/channels/1370798053899894926/1370856611287007384")

    def parse_emoji(self, spec: str | None):
        if not spec:
            return None
        if isinstance(spec, str):
            m = re.match(r"^<(a?):([A-Za-z0-9_~]+):(\d+)>$", spec.strip())
            if m:
                animated = bool(m.group(1))
                name = m.group(2)
                _id = int(m.group(3))
                return discord.PartialEmoji(animated=animated, name=name, id=_id)
            return spec
        return spec

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if os.getenv("ENVIRONMENT") in ["development", "custom"]:
            return

        guild = member.guild
        channel = guild.get_channel(self.WELCOME_CHANNEL_ID)
        if not channel:
            return

        view = discord.ui.View()
        link_button = discord.ui.Button(
            label=self.LINK_LABEL,
            url=self.LINK_URL,
            style=discord.ButtonStyle.link,
            emoji=self.parse_emoji(self.LINK_EMOJI_SPEC),
        )
        count_button = discord.ui.Button(
            style=discord.ButtonStyle.gray,
            label=f" {guild.member_count}",
            disabled=True,
            emoji=self.parse_emoji(self.COUNTER_EMOJI_SPEC),
        )
        view.add_item(link_button)
        view.add_item(count_button)

        for rid in [self.AUTO_ROLE_1_ID, self.AUTO_ROLE_2_ID]:
            if not rid:
                continue
            role = guild.get_role(int(rid))
            if role:
                try:
                    await member.add_roles(role)
                except (discord.Forbidden, discord.HTTPException):
                    pass

        content = f"Hello {member.mention}, welcome to **<:vrmt:1439704904854671371> Vermont State Roleplay**! We’re glad to have you here!"
        try:
            await channel.send(content, view=view)
        except (discord.Forbidden, discord.HTTPException):
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        lower = message.content.lower()
        if "vsrp sucks" in lower:
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
            try:
                await message.channel.send(f"{message.author.mention} - don't use naughty language!")
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(welcome(client))
