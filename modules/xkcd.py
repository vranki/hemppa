import os
import re
import html

import requests
from nio import AsyncClient, UploadError
from nio import UploadResponse

from modules.common.module import BotModule
from modules.common.exceptions import UploadFailed


class Xkcd:
    """
    Uses the XKCD (json) api https://xkcd.com/json.html to fetch web comics and metadata and display them in chats.
    """
    def __init__(self, title, img, alt, num):
        self.title = title
        self.img = img
        self.alt = alt
        self.num = num


    @staticmethod
    def create_from_json(json):
        return Xkcd(json.get("title"), json.get("img"), json.get("alt"), json.get("num"))

    def __str__(self):
        return "title: {} || explanation: {} || date: {} || original-url: {}".format(self.title,
                                                                                     self.explanation,
                                                                                     self.date,
                                                                                     self.hdurl)


class MatrixModule(BotModule):

    def __init__(self, name):
        super().__init__(name)
        self.uri_get_latest = 'https://xkcd.com/info.0.json'


    async def matrix_message(self, bot, room, event):
        self.logger.debug(f"room: {room.name} sender: {event.sender} queried the xkcd module with body: {event.body}")

        args = event.body.split()

        if len(args) == 1:
            await self.send_xkcd(bot, room, self.uri_get_latest)
        elif len(args) == 2:
            if args[1] == "help":
                await self.command_help(bot, room)
            else:
                xkcd_id = args[1]
                if re.match("\d+", date) is not None:
                    await self.send_xkcd(bot, room, self.uri_get_by_id(xkcd_id))
                else:
                    await bot.send_text(room, "Invalid comic id. ids must be positive integers.")

    async def send_xkcd(self, bot, room, uri):
        self.logger.debug(f"send request using uri {uri}")
        response = requests.get(uri)

        if response.status_code != 200:
            self.logger.error("unable to request api. response: [status: %d text: %s]", response.status_code, response.text)
            return await bot.send_text(room, "sorry. something went wrong accessing the api")

        xkcd = Xkcd.create_from_json(response.json())
        self.logger.debug(xkcd)

        img_url = xkcd.img
        try:
            matrix_uri = None
            matrix_uri, mimetype, w, h, size = bot.get_uri_cache(img_url)
        except (TypeError, ValueError):
            self.logger.debug(f"Not found in cache: {img_url}")
            try:
                matrix_uri, mimetype, w, h, size = await bot.upload_image(img_url)
            except (UploadFailed, TypeError, ValueError):
                await bot.send_text(room, f"Something went wrong uploading {apimg_url}.")

        await bot.send_html(room, f"<b>{html.escape(xkcd.title)} ({html.escape(xkcd.num)})</b>", f"{xkcd.title} ({xkcd.num})")
        await bot.send_image(room, matrix_uri, img_url, None, mimetype, w, h, size)
        await bot.send_text(room, f"{xkcd.alt}")

    def uri_get_by_id(self, id):
        return 'https://xkcd.com/' + int(id) + '/info.0.json'

    def help(self):
        return 'Sends latest/any specified XCKD web comic to the room. See https://xkcd.com/ '

    async def command_help(self, bot, room):
        msg = """commands:
        - no arguments: fetch latest xkcd comic
        - (\d+) fetch and display the xkcd comic with the given id
        - help - show command help
        """
        await bot.send_text(room, msg)

