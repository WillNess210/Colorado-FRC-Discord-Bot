import discord
import asyncio
from secrets import Secrets
from tba_help import TBA_Watcher, TBA_Teams_List_Generator


SECRET_FILENAME = '/src/secret.txt'
REFRESH_RATE = 180 # seconds

class FRCBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)

    async def on_ready(self):
        print('Colorado Bot Online')

    async def on_message(self, message):
        # Make sure the bot doesn't reply to itself.
        if message.author == client.user:
            return
        return



def get_secrets():
    try:
        with open(SECRET_FILENAME) as secret_file:
            return map(lambda x: x.strip(), secret_file.readlines())
    except IOError:
        raise IOError('Secret file not found. Create a file named "secret.txt"'
                      'in the "src" directory that holds your bot\'s secret.')


async def my_background_task(client):
    await client.wait_until_ready()
    channel = client.get_channel(Secrets.match_stream_channel)
    list_gen = TBA_Teams_List_Generator(Secrets.tba_auth_key)
    colorado_teams = list_gen.getTeamsFromState("Colorado")
    print(colorado_teams)
    tba_watcher = TBA_Watcher(Secrets.tba_auth_key, colorado_teams)
    await channel.send("Bot starting up.")
    while True:
        new_embeds = tba_watcher.getUpdates(channel)
        for embed in new_embeds:
            await channel.send(embed=embed)
        await asyncio.sleep(20) # task runs every 60 seconds

if __name__ == '__main__':
    Secrets.set_secrets(*get_secrets())

    client = FRCBot()
    client.loop.create_task(my_background_task(client))
    client.run(Secrets.bot_secret)