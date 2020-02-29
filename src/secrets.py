class Secrets:
    bot_secret = None

    @staticmethod
    def set_secrets(
        bot_secret,
    ):
        Secrets.bot_secret = bot_secret
