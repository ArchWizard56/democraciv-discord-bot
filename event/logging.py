import config
import discord
import datetime

from discord.ext import commands
from util.embed import embed_builder


# -- logging.py | event.logging --
#
# Logging module.
#


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -- Message Events --

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content == after.content:
            return
        if config.getConfig()['enableLogging']:
            if str(before.channel.id) not in config.getConfig()['excludedChannelsFromLogging']:
                if not before.clean_content or not after.clean_content:  # Removing this throws a http
                    # 400 bad request exception
                    return
                elif before.clean_content and after.clean_content:
                    guild = before.guild
                    channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
                    embed = embed_builder(title=':pencil2: Message Edited', description="")
                    embed.add_field(name='Author',
                                    value=before.author.mention + ' ' + before.author.name + '#'
                                                                + before.author.discriminator,
                                    inline=True)
                    embed.add_field(name='Channel', value=before.channel.mention, inline=True)
                    embed.add_field(name='Before', value=before.clean_content, inline=False)
                    embed.add_field(name='After', value=after.clean_content, inline=False)
                    embed.timestamp = datetime.datetime.utcnow()
                    await channel.send(embed=embed)
            else:
                return
        return

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if config.getConfig()['enableLogging']:
            if str(message.channel.id) not in config.getConfig()['excludedChannelsFromLogging']:
                guild = message.guild
                channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
                embed = embed_builder(title=':wastebasket: Message Deleted', description="")
                embed.add_field(name='Author',
                                value=message.author.mention + ' ' + message.author.name + '#'
                                                             + message.author.discriminator,
                                inline=True)
                embed.add_field(name='Channel', value=message.channel.mention, inline=True)

                if not message.embeds:
                    # If the deleted message is an embed, sending this new embed will raise an error as
                    # message.clean_content does not work with embeds
                    embed.add_field(name='Message', value=message.clean_content, inline=False)

                embed.timestamp = datetime.datetime.utcnow()
                await channel.send(content=None, embed=embed)
            else:
                return
        return

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        if config.getConfig()['enableLogging']:
            if str(payload.channel_id) not in config.getConfig()['excludedChannelsFromLogging']:
                guild = self.bot.get_guild(payload.guild_id)
                channel = self.bot.get_channel(payload.channel_id)
                log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
                embed = embed_builder(title=':wastebasket: :wastebasket: Bulk of Messages Deleted', description="")
                embed.add_field(name='Amount',
                                value=f'{len(payload.message_ids)}\n', inline=True)
                embed.add_field(name='Channel',
                                value=channel.mention, inline=True)
                embed.timestamp = datetime.datetime.utcnow()
                await log_channel.send(content=None, embed=embed)
            else:
                return
        return

    # -- Member Events --

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if config.getConfig()['enableWelcomeMessage']:
            guild = member.guild
            information_channel = discord.utils.get(guild.text_channels, name='information')
            help_channel = discord.utils.get(guild.text_channels, name='help')
            welcome_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['welcomeChannel'])

            # General case without mentioning anything in "{}" from the config's welcome_message
            if information_channel is None or help_channel is None:
                welcome_message = config.getStrings()['welcomeMessage']

            # Democraciv-specific case with mentioning {}'s
            else:
                welcome_message = config.getStrings()['welcomeMessage'].format(member=member.mention, guild=guild.name,
                                                                               information=information_channel.mention,
                                                                               help=help_channel.mention)
            await welcome_channel.send(welcome_message)

        if config.getConfig()['enableLogging']:
            guild = member.guild
            log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':tada: Member Joined', description="")
            embed.add_field(name='Member', value=member.mention)
            embed.add_field(name='Name', value=member.name + '#' + member.discriminator)
            embed.add_field(name='ID', value=member.id)
            embed.add_field(name='Mobile', value=member.is_on_mobile())
            embed.set_thumbnail(url=member.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            await log_channel.send(content=None, embed=embed)

        return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if config.getConfig()['enableLogging']:
            guild = member.guild
            channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':no_pedestrians: Member Left', description="")
            embed.add_field(name='Name', value=member.name + '#' + member.discriminator)
            embed.set_thumbnail(url=member.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            await channel.send(content=None, embed=embed)
        return

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if config.getConfig()['enableLogging']:
            if before.display_name != after.display_name:
                guild = before.guild
                log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
                embed = embed_builder(title=':arrows_counterclockwise: Nickname Changed', description="")
                embed.add_field(name='Member', value=before.mention + ' ' + before.name + '#' + before.discriminator,
                                inline=False)
                embed.add_field(name='Before', value=before.display_name)
                embed.add_field(name='After', value=after.display_name)
                embed.set_thumbnail(url=before.avatar_url)
                embed.timestamp = datetime.datetime.utcnow()
                await log_channel.send(content=None, embed=embed)

            if before.roles != after.roles:

                if len(before.roles) < len(after.roles):
                    for x in after.roles:
                        if x not in before.roles:
                            given_role = x.name
                    guild = before.guild
                    log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
                    embed = embed_builder(title=':sunglasses: Role given to Member', description="")
                    embed.add_field(name='Member',
                                    value=before.mention + ' ' + before.name + '#' + before.discriminator,
                                    inline=False)
                    embed.add_field(name='Role', value=given_role)
                    embed.set_thumbnail(url=before.avatar_url)
                    embed.timestamp = datetime.datetime.utcnow()
                    await log_channel.send(content=None, embed=embed)

                if len(before.roles) > len(after.roles):
                    for x in before.roles:
                        if x not in after.roles:
                            removed_role = x.name
                    guild = before.guild
                    log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
                    embed = embed_builder(title=':zipper_mouth: Role removed from Member', description="")
                    embed.add_field(name='Member',
                                    value=before.mention + ' ' + before.name + '#' + before.discriminator,
                                    inline=False)
                    embed.add_field(name='Role', value=removed_role)
                    embed.set_thumbnail(url=before.avatar_url)
                    embed.timestamp = datetime.datetime.utcnow()
                    await log_channel.send(content=None, embed=embed)
            else:
                return
        return

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if config.getConfig()['enableLogging']:
            channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':no_entry: Member Banned', description="")
            embed.add_field(name='Member', value=user.mention)
            embed.add_field(name='Name', value=user.name + '#' + user.discriminator)
            embed.set_thumbnail(url=user.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            await channel.send(content=None, embed=embed)
        return

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if config.getConfig()['enableLogging']:
            channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':dove: Member Unbanned', description="")
            embed.add_field(name='Member', value=user.mention)
            embed.add_field(name='Name', value=user.name + '#' + user.discriminator)
            embed.set_thumbnail(url=user.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            await channel.send(content=None, embed=embed)
        return

    # -- Guild Events --

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if config.getConfig()['enableLogging']:
            guild = role.guild
            log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':new: Role Created', description="")
            embed.add_field(name='Role', value=role.name)
            embed.add_field(name='Colour', value=role.colour)
            embed.add_field(name='ID', value=role.id, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await log_channel.send(content=None, embed=embed)
        return

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if config.getConfig()['enableLogging']:
            guild = role.guild
            log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':exclamation: Role Deleted', description="")
            embed.add_field(name='Role', value=role.name)
            embed.add_field(name='Creation Date',
                            value=datetime.datetime.strftime(role.created_at, "%d.%m.%Y, %H:%M:%S"))
            embed.add_field(name='ID', value=role.id, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await log_channel.send(content=None, embed=embed)
        return

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if config.getConfig()['enableLogging']:
            guild = channel.guild
            log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':new: Channel Created', description="")
            embed.add_field(name='Name', value=channel.mention)
            embed.add_field(name='Category', value=channel.category)
            embed.timestamp = datetime.datetime.utcnow()
            await log_channel.send(content=None, embed=embed)
        return

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if config.getConfig()['enableLogging']:
            guild = channel.guild
            log_channel = discord.utils.get(guild.text_channels, name=config.getConfig()['log_channel'])
            embed = embed_builder(title=':exclamation: Channel Deleted', description="")
            embed.add_field(name='Name', value=channel.name)
            embed.add_field(name='Category', value=channel.category)
            embed.timestamp = datetime.datetime.utcnow()
            await log_channel.send(content=None, embed=embed)
        return


def setup(bot):
    bot.add_cog(Log(bot))
