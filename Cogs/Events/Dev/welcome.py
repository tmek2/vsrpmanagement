import discord
from discord.ext import commands
from utils.emojis import *
import os
import re


class welcome(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))
        self.AUTO_ROLE_1_ID = int(os.getenv("AUTO_ROLE_1_ID", "0"))
        self.AUTO_ROLE_2_ID = int(os.getenv("AUTO_ROLE_2_ID", "0"))

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
        try:
            Config = await self.client.config.find_one({"_id": guild.id})
        except Exception:
            Config = None
        if not Config or not Config.get("Modules", {}).get("Welcome", False):
            return

        W = Config.get("Welcome", {})
        channel_id = W.get("channel_id") or self.WELCOME_CHANNEL_ID
        channel = guild.get_channel(channel_id) if channel_id else None
        if not channel:
            return
        perms = channel.permissions_for(guild.me)
        if not (perms.send_messages and perms.view_channel):
            return

        class WelcomeView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

        view = WelcomeView()

        def style_map(s: str):
            return {
                "Blurple": discord.ButtonStyle.blurple,
                "Green": discord.ButtonStyle.green,
                "Red": discord.ButtonStyle.red,
                "Grey": discord.ButtonStyle.gray,
            }.get((s or "Grey"), discord.ButtonStyle.gray)

        rep = {
            "{member}": member.name,
            "{member_mention}": member.mention,
            "{count}": guild.member_count,
        }

        from utils.format import Replace

        for b in W.get("buttons", [])[:25]:
            label = Replace(b.get("label", ""), rep)
            emoji = self.parse_emoji(b.get("emoji")) if b.get("emoji") else None
            disabled = bool(b.get("disabled", False))
            if b.get("type") == "link" and b.get("url"):
                try:
                    view.add_item(
                        discord.ui.Button(
                            label=label or "Link",
                            style=discord.ButtonStyle.link,
                            url=b.get("url"),
                            emoji=emoji,
                            disabled=disabled,
                        )
                    )
                except Exception:
                    continue
            elif b.get("type") == "button":
                style = style_map(b.get("style"))

                class Ack(discord.ui.Button):
                    def __init__(self, label, style, emoji, disabled):
                        super().__init__(label=label or "Button", style=style, emoji=emoji, disabled=disabled)

                    async def callback(self, i: discord.Interaction):
                        try:
                            await i.response.send_message(content=f"{tick} Welcome!", ephemeral=True)
                        except:
                            pass

                try:
                    view.add_item(Ack(label, style, emoji, disabled))
                except Exception:
                    continue

        roles_cfg = W.get("roles", [])
        env_roles = [self.AUTO_ROLE_1_ID, self.AUTO_ROLE_2_ID]
        roles_ids = roles_cfg if roles_cfg else [r for r in env_roles if r]
        assignable = [guild.get_role(int(r)) for r in roles_ids if r and guild.get_role(int(r))]
        if assignable:
            if guild.me and not guild.me.guild_permissions.manage_roles:
                assignable = []
            else:
                assignable = [r for r in assignable if r and r.position < guild.me.top_role.position]
            try:
                if assignable:
                    await member.add_roles(*assignable)
            except (discord.Forbidden, discord.HTTPException):
                pass

        content = W.get("message") or f"Welcome {member.mention}!"
        content = Replace(content, rep)
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
