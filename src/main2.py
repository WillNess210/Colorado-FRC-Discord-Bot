import discord
import asyncio

from secrets import Secrets
from frcpy import TBA_Request
from tba_help2 import FRC_Watcher

SECRET_FILENAME = '/src/secret.txt'

class FRCBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)
        
    async def on_ready(self):
        print('=== Colorado Discord Bot Online ===')

    async def on_message(self, message):
        if message.author == client.user:
            return

async def bg_task(client, tbar):
    await client.wait_until_ready()
    channels = [client.get_channel(ch) for ch in Secrets.match_stream_channels]
    frc_watcher = FRC_Watcher(tbar)
    frc_watcher.addTeamsFromState("Colorado")
    while True:
        print("Hello")
        to_send = frc_watcher.tick()
        for el in to_send:
            for channel in channels:
                await channel.send(el)
        await asyncio.sleep(5)

def get_secrets():
    try:
        with open(SECRET_FILENAME) as secret_file:
            return map(lambda x: x.strip(), secret_file.readlines())
    except IOError:
        raise IOError('Secret file not found. Create a file named "secret.txt"'
                      'in the "src" directory that holds your bot\'s secret.')

if __name__ == '__main__':
    Secrets.set_secrets(*get_secrets())

    tbar = TBA_Request(Secrets.tba_auth_key)

    client = FRCBot()
    client.loop.create_task(bg_task(client, tbar))
    client.run(Secrets.bot_secret)


