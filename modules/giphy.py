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
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) > 1:
            gif_url = "No image found"
            query = event.body[len(args[0])+1:]
            try:
                g = giphypop.Giphy(api_key=os.getenv("GIPHY_API_KEY"))
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

    def set_settings(self, data):
        super().set_settings(data)

    def help(self):
        return ('Giphy bot')
