class Secrets:
    bot_secret = None
    match_stream_channel = None
    tba_auth_key = None

    @staticmethod
    def set_secrets(
        bot_secret,
        match_stream_channel,
        tba_auth_key,
    ):
        Secrets.bot_secret = bot_secret
        Secrets.match_stream_channels = [int(ch) for ch in match_stream_channel.split(",")]
        Secrets.tba_auth_key = tba_auth_key
