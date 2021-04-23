import urllib.request
import urllib.parse
import urllib.error

import os
import giphypop
import requests
from nio import AsyncClient, UploadError
from nio import UploadResponse

from collections import namedtuple
from modules.common.module import BotModule

class MatrixModule(BotModule):
    api_key = None

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 3 and args[1] == 'apikey':
            bot.must_be_owner(event)

            self.api_key = args[2]
            bot.save_settings()
            await bot.send_text(room, 'Api key set')
        elif len(args) > 1:
            gif_url = "No image found"
            query = event.body[len(args[0])+1:]
            try:
                g = giphypop.Giphy(api_key=self.api_key)
                gifs = []
                try:
                    for x in g.search(phrase=query, limit=1):
                        gifs.append(x)
                except Exception:
                    pass
                if len(gifs) < 1:
                    await bot.send_text(room, gif_url)
                    return

                gif_url = gifs[0].media_url
                await bot.upload_and_send_image(room, gif_url)
                return
            except Exception as exc:
                gif_url = str(exc)
                await bot.send_text(room, gif_url)
        else:
            await bot.send_text(room, 'Usage: !giphy <query>')

    def get_settings(self):
        data = super().get_settings()
        data["api_key"] = self.api_key
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("api_key"):
            self.api_key = data["api_key"]

    def help(self):
        return ('Giphy bot')
