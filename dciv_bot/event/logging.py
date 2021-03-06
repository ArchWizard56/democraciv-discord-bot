import discord
import datetime
import dciv_bot.util.utils as utils

from dciv_bot.config import config
from discord.ext import commands


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_event(self, guild: discord.Guild, title: str, fields: dict, thumbnail: str = None,
                        to_owner: bool = False):

        if guild is None:
            return

        embed = self.bot.embeds.embed_builder(title=title, description="", has_footer=False)

        for field in fields:
            embed.add_field(name=field, value=fields[field][0], inline=fields[field][1])

        if thumbnail is not None:
            embed.set_thumbnail(url=thumbnail)

        # Send event embed to log channel
        log_channel = await utils.get_logging_channel(self.bot, guild)

        if log_channel is not None:
            await log_channel.send(embed=embed)

        if to_owner:
            embed.add_field(name='Guild', value=f"{guild.name} ({guild.id})", inline=False)
            await self.bot.owner.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild is None:
            return

        if not await self.bot.checks.is_logging_enabled(before.guild.id):
            return

        if not await self.bot.checks.is_channel_excluded(before.guild.id, before.channel.id):
            if not before.clean_content or not after.clean_content:
                return

            if before.content == after.content:
                return

            if before.embeds or after.embeds:
                return

            if len(before.content) > 1024 or len(after.content) > 1024:
                return

            embed_fields = {
                "Author": [f"{before.author.mention} {before.author}", False],
                "Channel": [f"{before.channel.mention}", True],
                "Jump": [f"[Link]({before.jump_url})", True],
                "Before": [f"{before.content}", False],
                "After": [f"{after.content}", False]
            }
            await self.log_event(before.guild, ":pencil2:  Message Edited", embed_fields)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return

        if not await self.bot.checks.is_logging_enabled(message.guild.id):
            return

        if not await self.bot.checks.is_channel_excluded(message.guild.id, message.channel.id):
            embed_fields = {
                "Author": [f"{message.author.mention} {message.author}", True],
                "Channel": [f"{message.channel.mention}", False]
            }

            if message.content and len(message.content) <= 1024:
                embed_fields['Message'] = [message.content, False]

            await self.log_event(message.guild, ':wastebasket:  Message Deleted', embed_fields)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        guild = self.bot.get_guild(payload.guild_id)

        if not await self.bot.checks.is_logging_enabled(guild.id):
            return

        if not await self.bot.checks.is_channel_excluded(guild.id, payload.channel_id):
            channel = self.bot.get_channel(payload.channel_id)

            embed_fields = {
                "Amount": [f"{len(payload.message_ids)}\n", True],
                "Channel": [f"{channel.mention}", True]
            }

            await self.log_event(guild, ':wastebasket: :wastebasket:  Bulk of Messages Deleted', embed_fields)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not await self.bot.checks.is_logging_enabled(member.guild.id):
            return

        embed_fields = {
            "Member": [f"{member.mention} {member}", False],
            "ID": [member.id, False]
        }

        await self.log_event(member.guild, ':tada:  Member Joined', embed_fields,
                             thumbnail=member.avatar_url_as(static_format="png"))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not await self.bot.checks.is_logging_enabled(member.guild.id):
            return

        embed_fields = {
            "Name": [str(member), False],
            "ID": [member.id, False]
        }

        await self.log_event(member.guild, ':no_pedestrians:  Member Left', embed_fields,
                             thumbnail=member.avatar_url_as(static_format="png"))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            if not await self.bot.checks.is_logging_enabled(before.guild.id):
                return

            embed_fields = {
                "Member": [f"{before.mention} {before}", False],
                "Before": [before.display_name, False],
                "After": [after.display_name, False]

            }

            await self.log_event(before.guild, ':arrows_counterclockwise:  Nickname Changed', embed_fields,
                                 thumbnail=before.avatar_url_as(static_format="png"))

        elif before.roles != after.roles:
            if not await self.bot.checks.is_logging_enabled(before.guild.id):
                return

            if len(before.roles) < len(after.roles):
                given_role = "*invalid role*"

                for x in after.roles:
                    if x not in before.roles:
                        given_role = x.name
                        break

                embed_fields = {
                    "Member": [f"{before.mention} {before}", False],
                    "Role": [given_role, False]
                }

                await self.log_event(before.guild, ':sunglasses:  Role given to Member', embed_fields,
                                     thumbnail=before.avatar_url_as(static_format="png"))

            elif len(before.roles) > len(after.roles):
                removed_role = "*invalid role*"

                for x in before.roles:
                    if x not in after.roles:
                        removed_role = x.name
                        break

                embed_fields = {
                    "Member": [f"{before.mention} {before}", False],
                    "Role": [removed_role, False]
                }

                await self.log_event(before.guild, ':zipper_mouth:  Role removed from Member', embed_fields,
                                     thumbnail=before.avatar_url_as(static_format="png"))

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not await self.bot.checks.is_logging_enabled(guild.id):
            return

        embed_fields = {
            "Name": [str(user), True]
        }

        await self.log_event(guild, ':no_entry:  Member Banned', embed_fields,
                             thumbnail=user.avatar_url_as(static_format="png"),
                             to_owner=True)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if not await self.bot.checks.is_logging_enabled(guild.id):
            return

        embed_fields = {
            "Name": [str(user), True]
        }

        await self.log_event(guild, ':dove:  Member Unbanned', embed_fields,
                             thumbnail=user.avatar_url_as(static_format="png"),
                             to_owner=True)

    # -- Guild Events --

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        introduction_channel = guild.system_channel or guild.text_channels[0]

        # Alert owner of this bot that the bot was invited to some place
        await self.bot.owner.send(f":warning:  I was added to {guild.name} ({guild.id}).")
        p = config.BOT_PREFIX

        introduction_message = f"Thanks for inviting me!\n\nYou can check `{p}help` or `{p}commands` to get more " \
                               f"information about me.\n\nUse the `{p}server` command to configure me for this server."\
                               f"\n\nIf you have any questions or suggestions, send a DM to {self.bot.owner.mention}!"

        # Send introduction message to random guild channel
        embed = self.bot.embeds.embed_builder(title=':two_hearts: Hey there!', description=introduction_message)

        # Add new guild to database
        await self.bot.db.execute("INSERT INTO guilds (id) VALUES ($1) ON CONFLICT DO NOTHING ", guild.id)
        await self.bot.cache.update_guild_config_cache()

        try:
            await introduction_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"[BOT] Got Forbidden while sending my introduction message on {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if not await self.bot.checks.is_logging_enabled(role.guild.id):
            return

        # Handle exception if bot was just added to new guild
        try:
            embed_fields = {
                "Role": [role.name, True],
                "Colour": [role.colour, True],
                "ID": [role.id, False]
            }

            await self.log_event(role.guild, ':new:  Role Created', embed_fields)

        except TypeError:
            return

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if not await self.bot.checks.is_logging_enabled(role.guild.id):
            return

        embed_fields = {
            "Role": [role.name, True],
            "Created On": [datetime.datetime.strftime(role.created_at, "%B %d, %Y"), True],
            "ID": [role.id, False]
        }

        await self.log_event(role.guild, ':exclamation:  Role Deleted', embed_fields)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not await self.bot.checks.is_logging_enabled(channel.guild.id):
            return

        embed_fields = {
            "Name": [channel.mention, True],
            "Category": [channel.category, True]
        }

        await self.log_event(channel.guild, ':new:  Channel Created', embed_fields)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not await self.bot.checks.is_logging_enabled(channel.guild.id):
            return

        embed_fields = {
            "Name": [channel.name, True],
            "Category": [channel.category, True]
        }

        await self.log_event(channel.guild, ':exclamation:  Channel Deleted', embed_fields)

    async def on_guild_remove(self, guild):
        await self.bot.owner.send(f":warning:  I was removed from {guild.name} ({guild.id}).")


def setup(bot):
    bot.add_cog(Log(bot))
