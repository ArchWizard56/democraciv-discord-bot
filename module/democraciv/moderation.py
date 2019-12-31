import discord
import datetime

from util import utils, mk
from config import config, token

from discord.ext import commands


class Moderation(commands.Cog):
    """Commands for the Mod Team"""

    def __init__(self, bot):
        self.bot = bot
        self.mod_request_channel = mk.MOD_REQUESTS_CHANNEL

    async def calculate_alt_chance(self, member: discord.Member, check_messages: bool = False) -> int:
        is_alt_chance = 0

        if member.bot:
            return 0

        discord_registration_duration_in_s = (datetime.datetime.utcnow() - member.created_at).total_seconds()
        hours_since = divmod(discord_registration_duration_in_s, 3600)[0]

        if hours_since <= 48:
            is_alt_chance += 0.1
            if hours_since <= 24:
                is_alt_chance += 0.2
                if hours_since <= 12:
                    is_alt_chance += 0.25
                    if hours_since <= 1:
                        is_alt_chance += 0.35

        weird_names = ["alt", "mysterious", "anonymous", "anon", "banned", "ban", "das", "mysterybox", "not",
                       "definitelynot"]

        if any(name in member.name.lower() for name in weird_names) or any(
                name in member.display_name.lower() for name in weird_names):
            is_alt_chance += 0.45

        default_avatars = ["https://cdn.discordapp.com/embed/avatars/0.png",
                           "https://cdn.discordapp.com/embed/avatars/1.png",
                           "https://cdn.discordapp.com/embed/avatars/2.png",
                           "https://cdn.discordapp.com/embed/avatars/3.png",
                           "https://cdn.discordapp.com/embed/avatars/4.png"]

        if member.avatar_url in default_avatars:
            is_alt_chance += 0.65

        if member.status != discord.Status.offline:
            if isinstance(member.web_status, discord.Status) and member.web_status != discord.Status.offline:
                is_alt_chance += 0.15
            elif isinstance(member.desktop_status, discord.Status) and member.desktop_status != discord.Status.offline:
                is_alt_chance += 0.05

        if member.premium_since is not None:
            is_alt_chance -= 2

        if len(member.activities) > 0:
            for act in member.activities:
                if act.type != 4:  # Custom Status
                    is_alt_chance -= 1.5
                    break

        if member.is_avatar_animated():
            is_alt_chance -= 2

        if check_messages:
            # This checks how often the member talked in the most common channels (#citizens, #welcome, #public-forum,
            # etc..)

            counter = 0
            citizens = self.bot.get_channel(208984105310879744)
            welcome = self.bot.get_channel(253009353601318912)
            helpchannel = self.bot.get_channel(466922441344548905)
            propaganda = self.bot.get_channel(636446062084620288)
            offtopic = self.bot.get_channel(208986320356376578)
            bot_channel = self.bot.get_channel(278254099768541204)
            public_forum = self.bot.get_channel(637016498535137340)

            channels = [citizens, welcome, helpchannel, propaganda, offtopic, bot_channel, public_forum]

            for i in range(6):
                async for message in channels[i].history(limit=500):
                    if message.author == member:
                        counter += 1

            if counter <= 20:
                is_alt_chance += 0.65

        return is_alt_chance

    @commands.Cog.listener(name="on_message")
    async def mod_request_listener(self, message):
        if message.guild != self.bot.democraciv_guild_object:
            return

        if message.channel.id != self.mod_request_channel:
            return

        if mk.get_moderation_role(self.bot) not in message.role_mentions:
            return

        embed = self.bot.embeds.embed_builder(title=":pushpin: New Request in #mod-requests",
                                              description=f"[Jump to message.]"
                                                          f"({message.jump_url}"
                                                          f")")
        embed.add_field(name="From", value=message.author.mention)
        embed.add_field(name="Request", value=message.content, inline=False)

        await mk.get_moderation_notifications_channel(self.bot).send(content=mk.get_moderation_role(self.bot).mention,
                                                                     embed=embed)

    @commands.Cog.listener(name="on_member_join")
    async def possible_alt_listener(self, member):
        if member.guild != self.bot.democraciv_guild_object:
            return

        if member.bot:
            return

        chance = await self.calculate_alt_chance(member, False)

        if chance >= 0.2:
            embed = self.bot.embeds.embed_builder(title="Possible Alt Account Joined", description="")
            embed.add_field(name="Member", value=member.mention, inline=False)
            embed.add_field(name="Member ID", value=member.id, inline=False)
            embed.add_field(name="Chance", value=f"There is a {chance * 100}% chance that {member} is an alt.")

            await mk.get_moderation_notifications_channel(self.bot).send(content=mk.get_moderation_role(self.bot)
                                                                         .mention, embed=embed)

    @commands.command(name='hub', aliases=['modhub', 'moderationhub', 'mhub'])
    @commands.has_role("Moderation")
    @utils.is_democraciv_guild()
    async def hub(self, ctx, ):
        """Link to the Moderation Hub"""
        link = token.MOD_HUB or 'Link not provided.'
        embed = self.bot.embeds.embed_builder(title="Moderation Hub", description=f"[Link]({link})")
        await ctx.message.add_reaction("\U0001f4e9")
        await ctx.author.send(embed=embed)

    @commands.command(name='alt')
    @commands.has_role("Moderation")
    @utils.is_democraciv_guild()
    async def alt(self, ctx, member: discord.Member):
        """Check if someone is an alt"""
        async with ctx.typing():
            chance = await self.calculate_alt_chance(member, True)

        embed = self.bot.embeds.embed_builder(title="Possible Alt Detection", description="This is in no way perfect "
                                                                                          "and should always be taken"
                                                                                          " with a grain of salt.")
        embed.add_field(name="Target", value=member.mention, inline=False)
        embed.add_field(name="Target ID", value=member.id, inline=False)
        embed.add_field(name="Result", value=f"There is a {chance * 100}% chance that {member} is an alt.")
        await ctx.send(embed=embed)

    @commands.command(name='registry')
    @commands.has_role("Moderation")
    @utils.is_democraciv_guild()
    async def registry(self, ctx):
        """Link to the Democraciv Registry"""
        link = token.REGISTRY or 'Link not provided.'
        embed = self.bot.embeds.embed_builder(title="Democraciv Registry", description=f"[Link]({link})")
        await ctx.message.add_reaction("\U0001f4e9")
        await ctx.author.send(embed=embed)

    @commands.command(name='drive', aliases=['googledrive', 'gdrive'])
    @commands.has_role("Moderation")
    @utils.is_democraciv_guild()
    async def gdrive(self, ctx):
        """Link to the Google Drive for MK6"""
        link = token.MK6_DRIVE or 'Link not provided.'
        embed = self.bot.embeds.embed_builder(title="Google Drive for MK6", description=f"[Link]({link})")
        await ctx.message.add_reaction("\U0001f4e9")
        await ctx.author.send(embed=embed)

    @commands.command(name='elections', aliases=['election', 'pins', 'electiontool', 'pintool'])
    @commands.has_role("Moderation")
    @utils.is_democraciv_guild()
    async def electiontool(self, ctx):
        """Link to DerJonas' Election Tool"""
        link = token.PIN_TOOL or 'Link not provided.'
        embed = self.bot.embeds.embed_builder(title="DerJonas' Election Tool", description=f"[Link]({link})")
        await ctx.message.add_reaction("\U0001f4e9")
        await ctx.author.send(embed=embed)

    @commands.command(name='kick')
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member"""
        if member == ctx.author:
            return await ctx.send(":x: You can't kick yourself.")

        if member == self.bot.DerJonas_object:
            #  :)
            return await ctx.send(":x: You can't kick that person.")

        if member == ctx.guild.me:
            return await ctx.send(":x: You can't kick me.")

        if reason:
            formatted_reason = f"Action requested by {ctx.author} with reason: {reason}"
        else:
            formatted_reason = f"Action requested by {ctx.author} with no specified reason."

        try:
            await ctx.guild.kick(member, reason=formatted_reason)
        except discord.Forbidden:
            return await ctx.send(":x: I'm not allowed to kick that person.")

        try:
            await member.send(f":no_entry: You were kicked from {ctx.guild.name}.")
        except discord.Forbidden:
            pass

        await ctx.send(f":white_check_mark: Successfully kicked {member}!")

    @commands.command(name='ban')
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: str, *, reason: str = None):
        """Ban a member

        If you want to ban a user that is not on this guild, use the user's ID: `-ban <id>`."""

        try:
            member_object = await commands.MemberConverter().convert(ctx, member)
            member_id = member_object.id
        except commands.BadArgument:
            try:
                member_id = int(member)
            except ValueError:
                member_id = None
            member_object = None

        if member_id is None:
            return await ctx.send(":x: I couldn't find that person.")

        if member_object == ctx.author:
            return await ctx.send(":x: You can't ban yourself.")

        if member_object == self.bot.DerJonas_object:
            #  :)
            return await ctx.send(":x: You can't ban that person.")

        if member_object == ctx.guild.me:
            return await ctx.send(":x: You can't ban me.")

        if reason:
            formatted_reason = f"Action requested by {ctx.author} with reason: {reason}"
        else:
            formatted_reason = f"Action requested by {ctx.author} with no specified reason."

        try:
            await ctx.guild.ban(discord.Object(id=member_id), reason=formatted_reason, delete_message_days=0)
        except discord.Forbidden:
            return await ctx.send(":x: I'm not allowed to ban that person.")
        except discord.HTTPException as e:
            return await ctx.send(":x: I couldn't find that person.")

        if member_object:
            try:
                await member_object.send(f":no_entry: You were banned from {ctx.guild.name}.")
            except discord.Forbidden:
                pass

        await ctx.send(f":white_check_mark: Successfully banned {member}!")

    @ban.error
    async def banerror(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(":x: I couldn't find that person.")

    @commands.command(name='unban')
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User, *, reason: str = None):
        """Unban a member"""

        if reason:
            formatted_reason = f"Action requested by {ctx.author} with reason: {reason}"
        else:
            formatted_reason = f"Action requested by {ctx.author} with no specified reason."

        try:
            await ctx.guild.unban(discord.Object(id=member.id), reason=formatted_reason)
        except discord.Forbidden:
            return await ctx.send(":x: I'm not allowed to unban that person.")
        except discord.HTTPException:
            return await ctx.send(":x: That person is not banned.")

        await ctx.send(f":white_check_mark: Successfully unbanned {member}!")

    @unban.error
    async def unbanerror(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(":x: I couldn't find that person.")


def setup(bot):
    bot.add_cog(Moderation(bot))
