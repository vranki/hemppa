import html
import requests

from modules.common.module import BotModule


class MatrixModule(BotModule):

    def __init__(self, name):
        super().__init__(name)
        self.url_generator_url = "https://inspirobot.me/api?generate=true"
        self.matrix_uri_cache = dict()

    async def matrix_message(self, bot, room, event):
        self.logger.debug(f"room: {room.name} sender: {event.sender} wants to be inspired!")

        args = event.body.split()

        if len(args) == 1:
            await self.send_inspiration(bot, room, self.url_generator_url)
            return
        elif len(args) == 2:
            if args[1] == "help":
                await self.command_help(bot, room)
                return
        await bot.send_text(room, f"unknown command: {args}")
        await self.command_help(bot, room)

    async def send_inspiration(self, bot, room, url_generator_url):
        self.logger.debug(f"Asking inspirobot for pic url at {url_generator_url}")
        response = requests.get(url_generator_url)

        if response.status_code != 200:
            self.logger.error("unable to request inspirobot api. response: [status: %d text: %s]", response.status_code, response.text)
            return await bot.send_text(room, f"sorry. something went wrong accessing inspirobot: {response.status_code}: {response.text}")

        pic_url = response.text
        self.logger.debug("Sending image with src='%s'", pic_url)
        await bot.upload_and_send_image(room, pic_url)

    def help(self):
        return """I'm InspiroBot.
        I am an artificial intelligence dedicated to generating unlimited amounts of unique inspirational quotes
        for endless enrichment of pointless human existence.
        https://inspirobot.me/
        """

    async def command_help(self, bot, room):
        msg = """usage: !inspire [command]
        No command to generate an inspirational poster just for you!
        - help - show this. Useful, isn't it?
        """
        await bot.send_html(room, f"<b>{html.escape(self.help())}</b>", self.help())
        await bot.send_text(room, msg)
