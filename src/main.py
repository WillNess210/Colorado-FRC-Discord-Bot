import discord
from secrets import Secrets

SECRET_FILENAME = '/src/secret.txt'

class FRCBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)

    async def on_ready(self):
        print('Colorado Bot Online')

    async def on_message(self, message):
        # Make sure the bot doesn't reply to itself.
        if message.author == client.user:
            return
        print('received:', message.content)


def get_secrets():
    try:
        with open(SECRET_FILENAME) as secret_file:
            return map(lambda x: x.strip(), secret_file.readlines())
    except IOError:
        raise IOError('Secret file not found. Create a file named "secret.txt"'
                      'in the "src" directory that holds your bot\'s secret.')


if __name__ == '__main__':
    import os.path
    from os import path
    print(path.exists("/src/secret.txt"))



    Secrets.set_secrets(*get_secrets())

    client = FRCBot()
    client.run(Secrets.bot_secret)
