import sys
import json
import praw
import config
import discord
import asyncio
import datetime
import requests
import traceback
import discord.utils
import pkg_resources

from discord.ext import commands

# -- Discord Bot for the r/Democraciv Server --
#
# Author: DerJonas
# Interpreter: Python3.7
# Library: discord.py 1.2.2
# License: MIT
# Source: https://github.com/jonasbohmann/democraciv-discord-bot
#


# -- client.py --
#
# Main part of the bot. Loads all modules on startup. Remove or add new modules by adding or removing them to/from
# "initial_extensions".
#
# All things relevant to event logging are handled here as well.
#

client = commands.Bot(command_prefix=config.getPrefix(), description=config.getConfig()['botDescription'],
                      case_insensitive=True)
author = discord.AppInfo.owner

# -- Twitch --
activeStream = False

# -- Reddit --
if config.getReddit()["enableRedditAnnouncements"]:
    reddit = praw.Reddit(client_id=config.getTokenFile()['redditClientID'],
                         client_secret=config.getTokenFile()['redditClientSecret'],
                         user_agent=config.getReddit()['userAgent'])

    subreddit = reddit.subreddit(config.getReddit()['subreddit'])
    last_reddit_post = config.getLastRedditPost()

# -- Cogs --
initial_extensions = ['module.link',
                      'module.about',
                      'module.vote',
                      'module.time',
                      'module.fun',
                      'module.admin',
                      'module.parties',
                      'module.help',
                      'module.wikipedia',
                      'module.random',
                      'module.role',
                      'event.logging',
                      'event.error_handler']


# -- Reddit --
# Background task that gets new posts from r/democraciv every 30 seconds

async def reddit_task():
    await client.wait_until_ready()

    try:
        dcivGuild = client.get_guild(int(config.getConfig()["homeServerID"]))
        channel = discord.utils.get(dcivGuild.text_channels, name=config.getReddit()['redditAnnouncementChannel'])
    except AttributeError:
        print(
            f'ERROR - I could not find the Democraciv Discord Server! Change "homeServerID" '
            f'in the config to a server I am in or disable Reddit announcements.')
        return

    while not client.is_closed():
        for submission in subreddit.new(limit=1):
            reddit_post = submission
            title = submission.title
            author = submission.author
            comments_link = submission.permalink

        if not last_reddit_post['id'] == submission.id:
            # Set new last_reddit_post
            config.getLastRedditPost()['id'] = submission.id
            config.setLastRedditPost()

            embed = discord.Embed(title=f":mailbox_with_mail: New post on r/{config.getReddit()['subreddit']}",
                                  colour=0x7f0000)
            embed.add_field(name="Thread", value=f"[{title}](https://reddit.com{comments_link})", inline=False)
            embed.add_field(name="Author", value=f"u/{author}", inline=False)

            # Fetch image of post if it has one
            index = 4
            image_link = None
            for x in range(3):
                if image_link is not None:
                    embed.set_thumbnail(url=image_link)
                    print(image_link)
                    break
                try:
                    image_link = reddit_post.preview['images'][0]['resolutions'][index]['url']
                except (AttributeError, UnboundLocalError, IndexError) as e:
                    index = index - 1

            embed.set_footer(text=config.getConfig()['botName'], icon_url=config.getConfig()['botIconURL'])
            embed.timestamp = datetime.datetime.utcnow()

            await channel.send(embed=embed)
        await asyncio.sleep(30)


# -- Twitch --
# HTTP request to the Twitch API for twitch_task

def checkTwitchLivestream():
    twitchAPIUrl = "https://api.twitch.tv/helix/streams?user_login=" + config.getTwitch()['twitchChannelName']
    newTwitchAPIToken = config.getTokenFile()['twitchAPIKey']
    httpHeader = {'Client-ID': newTwitchAPIToken}
    twitchRequest = requests.get(twitchAPIUrl, headers=httpHeader)
    twitch = json.loads(twitchRequest.content)
    global activeStream

    try:
        twitch['data'][0]['id']
    except (IndexError, KeyError) as e:
        activeStream = False
        return False

    thumbnail = twitch['data'][0]['thumbnail_url'].replace('{width}', '720').replace('{height}', '380')
    return [twitch['data'][0]['title'], thumbnail]


# -- Twitch  --
# Background task that posts an alert if twitch.tv/democraciv is live

async def twitch_task():
    await client.wait_until_ready()
    global activeStream
    streamer = config.getTwitch()['twitchChannelName']

    try:
        dcivGuild = client.get_guild(int(config.getConfig()["homeServerID"]))
        channel = discord.utils.get(dcivGuild.text_channels, name=config.getTwitch()['twitchAnnouncementChannel'])
    except AttributeError:
        print(
            f'ERROR - I could not find the Democraciv Discord Server! Change "homeServerID" '
            f'in the config to a server I am in or disable Twitch announcements.')
        return

    while not client.is_closed():
        twitch_data = checkTwitchLivestream()
        if twitch_data is not False:
            if activeStream is False:
                activeStream = True
                embed = discord.Embed(title=f":satellite: {streamer} - Live on Twitch", colour=0x7f0000)
                embed.add_field(name="Title", value=twitch_data[0], inline=False)
                embed.add_field(name="Link", value=f"https://twitch.tv/{streamer}", inline=False)
                embed.set_image(url=twitch_data[1])
                embed.set_footer(text=config.getConfig()['botName'], icon_url=config.getConfig()['botIconURL'])
                embed.timestamp = datetime.datetime.utcnow()
                if config.getTwitch()['everyonePingOnAnnouncement']:
                    await channel.send(f'@everyone {streamer} is live on Twitch!')
                await channel.send(embed=embed)
        await asyncio.sleep(60)


@client.event
async def on_ready():
    print('Logged in as ' + client.user.name + ' with discord.py ' + str(
        pkg_resources.get_distribution('discord.py').version))
    print('-------------------------------------------------------')
    if config.getTwitch()['enableTwitchAnnouncements']:
        client.loop.create_task(twitch_task())

    if config.getReddit()['enableRedditAnnouncements']:
        client.loop.create_task(reddit_task())

    await client.change_presence(
        activity=discord.Game(name=config.getPrefix() + 'help | Watching over r/Democraciv'))


@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        return
    if message.author.bot:
        return

    # WIP DemocraCorp Ban
    # (in case we need this in the future)

    # banned_dcorp_words = ['democracorp', 'dcorp', 'vote buying', 'fair votes', 'fair votes act', '#dc-discussion', 'dc',' round table', 'dc debate', 'vote bought', 'bougth votes', 'storting bought']

    # message_content = message.clean_content.lower()

    # if any(words in message_content for words in banned_dcorp_words):
    #    await message.delete()
    #    await message.channel.send(':x: Discussion about anything related to Democracorp has been banned.')

    await client.process_commands(message)


if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
            print('Successfully loaded ' + extension)
        except Exception as e:
            print(f'Failed to load module {extension}.', file=sys.stderr)
            traceback.print_exc()

try:
    client.run(config.getToken(), reconnect=True, bot=True)
except asyncio.TimeoutError as e:
    print(f'ERROR - TimeoutError\n{e}')
