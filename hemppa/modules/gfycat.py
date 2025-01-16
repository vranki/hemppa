import urllib.request
import urllib.parse
import urllib.error

import requests
from nio import AsyncClient, UploadError
from nio import UploadResponse

from collections import namedtuple
from modules.common.module import BotModule

class gfycat(object):
    """
    A very simple module that allows you to
    1. search a gif on gfycat from a remote location
    """

    # Urls
    url = "https://api.gfycat.com"

    def __init__(self):
        super(gfycat, self).__init__()

    def __fetch(self, url, param):
        import json
        try:
            # added simple User-Ajent string to avoid CloudFlare block this request
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url+param, headers=headers)
            connection = urllib.request.urlopen(req).read()
        except urllib.error.HTTPError as err:
            raise ValueError(err.read())
        result = namedtuple("result", "raw json")
        return result(raw=connection, json=json.loads(connection))

    def search(self, param):
        result = self.__fetch(self.url, "/v1/gfycats/search?search_text=%s" % urllib.parse.quote_plus(param))
        if "errorMessage" in result.json:
            raise ValueError("%s" % self.json["errorMessage"])
        return _gfycatSearch(result)

class _gfycatUtils(object):

    """
    A utility class that provides the necessary common
    for all the other classes
    """

    def __init__(self, param, json):
        super(_gfycatUtils, self).__init__()
        # This can be used for other functions related to this class
        self.res = param
        self.js = json

    def raw(self):
        return self.res.raw

    def json(self):
        return self.js

    def __len__(self):
        return len(self.js)

    def get(self, what):
        try:
            return self.js[what]
        except KeyError as error:
            return ("Sorry, can't find %s" % error)

class _gfycatSearch(_gfycatUtils):

    """
    This class will provide more information for an existing url
    """

    def __init__(self, param):
        super(_gfycatSearch, self).__init__(param, param.json["gfycats"])

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) > 1:
            gif_url = "No image found"
            query = event.body[len(args[0])+1:]
            try:
                gifs = gfycat().search(query)
                if len(gifs) < 1:
                    await bot.send_text(room, gif_url)
                    return

                gif_url = gifs.get(0)["content_urls"]["largeGif"]["url"]
                await bot.upload_and_send_image(room, gif_url)
            except Exception as exc:
                gif_url = str(exc)
                await bot.send_text(room, gif_url)
        else:
            await bot.send_text(room, 'Usage: !gfycat <query>')

    def help(self):
        return ('Gfycat bot')
