import discord
import asyncio
from secrets import Secrets
from tba_help import TBA_Watcher, TBA_Teams_List_Generator
from time import time

SECRET_FILENAME = '/src/secret.txt'
REFRESH_RATE = 180 # seconds
TEAM_SUMMARY_REFRESH_RATE = 60 * 30 #seconds

class FRCBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)
        self.printStatus = True

    async def on_ready(self):
        print('Colorado Bot Online')

    async def on_message(self, message):
        # Make sure the bot doesn't reply to itself.
        if message.author == client.user:
            return
        if message.content == "!status" and message.channel.id in Secrets.match_stream_channels:
            print("received status request")
            self.printStatus = True
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
    channels = [client.get_channel(ch) for ch in Secrets.match_stream_channels]
    list_gen = TBA_Teams_List_Generator(Secrets.tba_auth_key)
    colorado_teams = list_gen.getTeamsFromState("Colorado")
    print(colorado_teams)
    tba_watcher = TBA_Watcher(Secrets.tba_auth_key, colorado_teams)
    for channel in channels:
        await channel.send("Bot starting up.")
    last_team_summary = -1
    update_data = None
    while True:
        new_embeds = tba_watcher.getUpdates()
        for channel in channels:
            for embed in new_embeds:
                await channel.send(embed=embed)
                await asyncio.sleep(0.5) # wait 1 second between every message
        if len(tba_watcher.events) > 0 and (time() - last_team_summary > TEAM_SUMMARY_REFRESH_RATE or client.printStatus):
            last_team_summary = time()
            summary, update_data = tba_watcher.getTeamUpdates(last_update_data=(None if client.printStatus else update_data))
            client.printStatus = False
            if summary != None:
                for channel in channels:
                    await channel.send(embed=summary)
            else:
                print("suppressed status print - no changes")
        elif len(tba_watcher.events) == 0 and client.printStatus:
            client.printStatus = False
            await channel.send("No teams currently in events.")
        await asyncio.sleep(20) # task runs every 60 seconds

if __name__ == '__main__':
    Secrets.set_secrets(*get_secrets())

    client = FRCBot()
    client.loop.create_task(my_background_task(client))
    client.run(Secrets.bot_secret)