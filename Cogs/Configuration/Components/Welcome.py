import discord
from utils.emojis import *
from utils.HelpEmbeds import NotYourPanel


async def WelcomeEmbed(interaction: discord.Interaction, Config: dict, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = (
        "> Configure automated welcome messages. Use variables in your text to personalize messages.\n"
        ">\n"
        "> Variables:\n"
        "> • `{member}` — the user's username\n"
        "> • `{member_mention}` — mentions the user\n"
        "> • `{count}` — total members in the server (bots + humans)\n"
        ">\n"
        "> Buttons support labels, emojis, types (link or button), enabled/disabled, and `{count}` in labels."
    )
    return embed


class WelcomeOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            placeholder="Welcome Configuration",
            options=[
                discord.SelectOption(label="Message", emoji=discord.PartialEmoji.from_str("<:message:1438995939313320038>")),
                discord.SelectOption(label="Channel", emoji=discord.PartialEmoji.from_str("<:tag:1438996042057256961>")),
                discord.SelectOption(label="Buttons", emoji=discord.PartialEmoji.from_str("<:button:1438995847928090765>")),
                discord.SelectOption(label="Roles", emoji=discord.PartialEmoji.from_str("<:permissions:1438995968237375579>")),
                discord.SelectOption(label="Preview", emoji=discord.PartialEmoji.from_str("<:list:1438962364505395370>")),
            ],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        selection = self.values[0]
        if selection == "Channel":
            view = discord.ui.View()
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
            current = interaction.guild.get_channel(Config.get("Welcome", {}).get("channel_id", 0))
            view.add_item(WelcomeChannel(interaction.user, current))
            return await interaction.followup.send(view=view, ephemeral=True)

        if selection == "Message":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
            current = (Config.get("Welcome", {}).get("message") or "")
            view = WelcomeMessageEditor(interaction.user, current)
            return await interaction.followup.send(view=view, ephemeral=True)

        if selection == "Buttons":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
            buttons = Config.get("Welcome", {}).get("buttons", [])
            view = WelcomeButtonManager(interaction.user, buttons)
            return await interaction.followup.send(view=view, ephemeral=True)

        if selection == "Preview":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
            W = Config.get("Welcome", {})
            content = W.get("message") or f"Welcome {interaction.user.mention}!"
            rep = {
                "{member}": interaction.user.name,
                "{member_mention}": interaction.user.mention,
                "{count}": interaction.guild.member_count,
            }
            from utils.format import Replace
            content = Replace(content, rep)
            view = build_buttons_view(interaction, W.get("buttons", []), rep)
            return await interaction.followup.send(content=content, view=view, ephemeral=True)

        if selection == "Roles":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
            R = Config.get("Welcome", {}).get("roles", [])
            defaults = [interaction.guild.get_role(r) for r in R if interaction.guild.get_role(r)]
            view = discord.ui.View()
            view.add_item(WelcomeRoles(interaction.user, defaults))
            return await interaction.followup.send(view=view, ephemeral=True)


class WelcomeChannel(discord.ui.ChannelSelect):
    def __init__(self, author: discord.Member, current: discord.TextChannel | None):
        super().__init__(
            placeholder="Select channel",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            default_values=[current] if current else [],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        selected = self.values[0] if self.values else None
        channel = (
            interaction.guild.get_channel(selected.id) if selected else None
        )
        if not channel:
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name},** invalid channel selected.",
                ephemeral=True,
            )
        perms = channel.permissions_for(interaction.guild.me)
        if not (perms.send_messages and perms.view_channel):
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name},** I don't have permission in {channel.mention}.",
                ephemeral=True,
            )
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
        if not Config.get("Welcome"):
            Config["Welcome"] = {}
        Config["Welcome"]["channel_id"] = channel.id
        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": Config}, upsert=True)
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** channel updated.",
            ephemeral=True,
        )


class WelcomeRoles(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, defaults: list):
        super().__init__(
            placeholder="Select up to 2 roles",
            min_values=0,
            max_values=2,
            default_values=defaults[:2] if defaults else [],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        me = interaction.guild.me
        if not me.guild_permissions.manage_roles:
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name},** I need Manage Roles permission to assign roles.",
                ephemeral=True,
            )
        roles = list(self.values)[:2] if self.values else []
        invalid = [r for r in roles if r.position >= me.top_role.position]
        assignable = [r for r in roles if r.position < me.top_role.position]
        selected = [r.id for r in assignable]
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
        if not Config.get("Welcome"):
            Config["Welcome"] = {}
        Config["Welcome"]["roles"] = selected
        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": Config}, upsert=True)
        msg = f"{tick} **{interaction.user.display_name},** roles updated."
        if invalid:
            msg += "\n" + f"{no} Cannot assign: " + ", ".join([r.mention for r in invalid])
        await interaction.followup.send(content=msg, ephemeral=True)


class WelcomeMessageEditor(discord.ui.View):
    def __init__(self, author: discord.Member, current: str):
        super().__init__(timeout=600)
        self.author = author
        self.current = current or ""

    @discord.ui.button(label="Content", style=discord.ButtonStyle.gray, emoji=discord.PartialEmoji.from_str("<:message:1438995939313320038>"))
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(embed=NotYourPanel(), ephemeral=True)
        await interaction.response.send_modal(MessageModal(self))

    @discord.ui.button(label="{member}", style=discord.ButtonStyle.blurple)
    async def insert_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._insert(interaction, "{member}")

    @discord.ui.button(label="{member_mention}", style=discord.ButtonStyle.blurple)
    async def insert_mention(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._insert(interaction, "{member_mention}")

    @discord.ui.button(label="{count}", style=discord.ButtonStyle.blurple)
    async def insert_count(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._insert(interaction, "{count}")

    async def _insert(self, interaction: discord.Interaction, token: str):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        self.current = (self.current or "") + (" " if self.current else "") + token
        await interaction.followup.send(content=f"Updated: {self.current}", ephemeral=True)

    @discord.ui.button(label="Save", style=discord.ButtonStyle.green, emoji=save)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
        if not Config.get("Welcome"):
            Config["Welcome"] = {}
        # basic sanitization
        content = (self.current or "").strip()
        content = content[:2000]
        Config["Welcome"]["message"] = content
        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": Config}, upsert=True)
        await interaction.followup.send(content=f"{tick} **{interaction.user.display_name},** message saved.", ephemeral=True)


class MessageModal(discord.ui.Modal, title="Message"):
    def __init__(self, editor: WelcomeMessageEditor):
        super().__init__()
        self.editor = editor
        self.content = discord.ui.TextInput(
            label="Content",
            style=discord.TextStyle.long,
            required=False,
            max_length=2000,
            default=self.editor.current or "",
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.editor.current = self.content.value
        await interaction.followup.send(content="Updated.", ephemeral=True)


class WelcomeButtonManager(discord.ui.View):
    def __init__(self, author: discord.Member, buttons: list):
        super().__init__(timeout=600)
        self.author = author
        self.buttons = buttons or []

    @discord.ui.button(label="Add Link", style=discord.ButtonStyle.gray, emoji=discord.PartialEmoji.from_str("<:link:1438995921173217441>"))
    async def add_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddLinkButton(self))

    @discord.ui.button(label="Add Button", style=discord.ButtonStyle.gray, emoji=discord.PartialEmoji.from_str("<:button:1438995847928090765>"))
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddRegularButton(self))

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red, emoji=discord.PartialEmoji.from_str("<:subtract:1438996031168708618>"))
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        if len(self.buttons) == 0:
            return await interaction.followup.send(content=f"{no} **{interaction.user.display_name},** no buttons.", ephemeral=True)
        options = [
            discord.SelectOption(label=b.get("label","Unnamed"), value=str(ix))
            for ix, b in enumerate(self.buttons[:25])
        ]
        view = discord.ui.View()
        view.add_item(RemoveButton(self.author, self, options))
        await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(label="Preview", style=discord.ButtonStyle.blurple, emoji=discord.PartialEmoji.from_str("<:list:1438962364505395370>"))
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        rep = {
            "{member}": interaction.user.name,
            "{member_mention}": interaction.user.mention,
            "{count}": interaction.guild.member_count,
        }
        view = build_buttons_view(interaction, self.buttons, rep)
        await interaction.followup.send(content="Button preview", view=view, ephemeral=True)

    @discord.ui.button(label="Save", style=discord.ButtonStyle.green, emoji=save)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {"_id": interaction.guild.id}
        if not Config.get("Welcome"):
            Config["Welcome"] = {}
        Config["Welcome"]["buttons"] = self.buttons
        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": Config}, upsert=True)
        await interaction.followup.send(content=f"{tick} **{interaction.user.display_name},** buttons saved.", ephemeral=True)


class RemoveButton(discord.ui.Select):
    def __init__(self, author: discord.Member, manager: WelcomeButtonManager, options: list):
        super().__init__(options=options)
        self.author = author
        self.manager = manager

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        idx = int(self.values[0])
        if 0 <= idx < len(self.manager.buttons):
            self.manager.buttons.pop(idx)
        await interaction.followup.send(content="Removed.", ephemeral=True)


class AddLinkButton(discord.ui.Modal, title="Add Link Button"):
    def __init__(self, manager: WelcomeButtonManager):
        super().__init__()
        self.manager = manager
        self.label = discord.ui.TextInput(label="Label", max_length=80)
        self.url = discord.ui.TextInput(label="URL", max_length=2048)
        self.emoji = discord.ui.TextInput(label="Emoji", required=False)
        self.enabled = discord.ui.TextInput(label="Enabled (True/False)", required=False)
        self.add_item(self.label)
        self.add_item(self.url)
        self.add_item(self.emoji)
        self.add_item(self.enabled)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = self.url.value.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return await interaction.followup.send(content=f"{no} **{interaction.user.display_name},** URL must start with http(s).", ephemeral=True)
        enabled = (self.enabled.value or "True").lower() == "true"
        self.manager.buttons.append({
            "type": "link",
            "label": self.label.value.strip(),
            "url": url,
            "emoji": (self.emoji.value.strip() or None),
            "disabled": (not enabled),
        })
        await interaction.followup.send(content="Added.", ephemeral=True)


class AddRegularButton(discord.ui.Modal, title="Add Button"):
    def __init__(self, manager: WelcomeButtonManager):
        super().__init__()
        self.manager = manager
        self.label = discord.ui.TextInput(label="Label", max_length=80)
        self.style = discord.ui.TextInput(label="Style (Blurple, Green, Red, Grey)", required=False)
        self.emoji = discord.ui.TextInput(label="Emoji", required=False)
        self.enabled = discord.ui.TextInput(label="Enabled (True/False)", required=False)
        self.add_item(self.label)
        self.add_item(self.style)
        self.add_item(self.emoji)
        self.add_item(self.enabled)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        style = (self.style.value or "Grey").capitalize()
        if style not in ["Blurple", "Green", "Red", "Grey"]:
            return await interaction.followup.send(content=f"{no} **{interaction.user.display_name},** invalid style.", ephemeral=True)
        enabled = (self.enabled.value or "True").lower() == "true"
        self.manager.buttons.append({
            "type": "button",
            "label": self.label.value.strip(),
            "style": style,
            "emoji": (self.emoji.value.strip() or None),
            "disabled": (not enabled),
        })
        await interaction.followup.send(content="Added.", ephemeral=True)


def build_buttons_view(interaction: discord.Interaction, buttons: list, replacements: dict):
    class Dummy(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

    view = Dummy()

    def parse_emoji(spec: str | None):
        if not spec:
            return None
        try:
            return discord.PartialEmoji.from_str(spec)
        except discord.DiscordException:
            return None

    style_map = {
        "Blurple": discord.ButtonStyle.blurple,
        "Green": discord.ButtonStyle.green,
        "Red": discord.ButtonStyle.red,
        "Grey": discord.ButtonStyle.gray,
    }

    from utils.format import Replace
    for b in buttons[:25]:
        label = Replace(b.get("label", "Unnamed"), replacements)
        emoji = parse_emoji(b.get("emoji")) if b.get("emoji") else None
        disabled = bool(b.get("disabled", False))
        if b.get("type") == "link" and b.get("url"):
            try:
                view.add_item(
                    discord.ui.Button(
                        label=label,
                        style=discord.ButtonStyle.link,
                        url=b.get("url"),
                        emoji=emoji,
                        disabled=disabled,
                    )
                )
            except:
                continue
        elif b.get("type") == "button":
            style = style_map.get(b.get("style", "Grey"), discord.ButtonStyle.gray)

            class Ack(discord.ui.Button):
                def __init__(self, label, style, emoji, disabled):
                    super().__init__(label=label, style=style, emoji=emoji, disabled=disabled)

                async def callback(self, i: discord.Interaction):
                    try:
                        await i.response.send_message(content=f"{tick} Welcome!", ephemeral=True)
                    except:
                        pass

            try:
                view.add_item(Ack(label, style, emoji, disabled))
            except:
                continue
    return view