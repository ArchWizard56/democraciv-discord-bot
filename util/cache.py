import asyncio


class Cache:
    def __init__(self, bot):
        self.bot = bot
        self.guild_config = None
        self.bot.loop.create_task(self.update_guild_config_cache())

    async def verify_guild_config_cache(self, message):
        if message.guild is None:
            return

        if message.guild.id not in self.guild_config:
            if not await self.bot.checks.is_guild_initialized(message.guild.id):
                print(f"[DATABASE] Guild {message.guild.name} ({message.guild.id}) was not initialized. "
                      f"Adding default entry to database... ")
                await self.bot.db.execute("INSERT INTO guilds (id) VALUES ($1)", message.guild.id)
                print(f"[DATABASE] Successfully initialized guild {message.guild.name} ({message.guild.id})")

            await self.update_guild_config_cache()

    async def update_guild_config_cache(self):
        await self.bot.wait_until_ready()

        if self.bot.db is None:
            await asyncio.sleep(5)

        records = await self.bot.db.fetch("SELECT * FROM guilds")
        guild_config = dict()

        for record in records:
            config = {"welcome": record['welcome'],
                      "welcome_message": record['welcome_message'],
                      "welcome_channel": record['welcome_channel'],
                      "logging": record['logging'],
                      "logging_channel": record['logging_channel'],
                      "logging_excluded": record['logging_excluded'],
                      "defaultrole": record['defaultrole'],
                      "defaultrole_role": record['defaultrole_role'],
                      "tag_creation_allowed": record['tag_creation_allowed']
                      }

            guild_config[record['id']] = config

        self.guild_config = guild_config
        print("[CACHE] Guild config cache was updated.")

    async def get_guild_config_cache(self, guild_id: int, setting: str):
        try:
            cached = self.guild_config[guild_id][setting]
        except (TypeError, KeyError) as e:
            await self.bot.owner.send(f":x: Error in Cache.get_guild_config_cache({guild_id}, {setting})"
                                      f"\n{e.__class__.__name__}: {e}")
            cached = None

        if cached is None:
            fetched = await self.bot.db.fetchval("SELECT $2 FROM guilds WHERE id = $1", guild_id, setting)

            return fetched
        else:
            return cached
