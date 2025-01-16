import time
import urllib.request
import urllib.parse
import urllib.error

import aiohttp.web
import requests
import os
import json
import asyncio
from aiohttp import web
from future.moves.urllib.parse import urlencode
from nio import MatrixRoom

from modules.common.module import BotModule

import nest_asyncio
nest_asyncio.apply()

rooms = dict()
global_bot = None

send_entry_lock = asyncio.Lock()


async def send_entry(blob, content_type, fmt_params, rooms):
    async with send_entry_lock:
        for room_id in rooms:
            room = MatrixRoom(room_id=room_id, own_user_id=os.getenv("BOT_OWNERS"),
                              encrypted=rooms[room_id])
            if blob and content_type:
                await global_bot.upload_and_send_image(room, blob, text="", blob=True, blob_content_type=content_type)

            await global_bot.send_html(room, msg_template_html.format(**fmt_params),
                                       msg_template_plain.format(**fmt_params))


def get_image(img=None, width=1000, height=1500):
    """
    Return image data as array.
    Array contains the image content type and image binary

    Parameters required:    img { Plex image location }
    Optional parameters:    width { the image width }
                            height { the image height }
    Output: array
    """

    pms_url = os.getenv("PLEX_MEDIA_SERVER_URL")
    pms_token = os.getenv("PLEX_MEDIA_SERVER_TOKEN")
    if not pms_url or not pms_token:
        return None

    width = width or 1000
    height = height or 1500

    if img:
        params = {'url': 'http://127.0.0.1:32400%s' % (img), 'width': width, 'height': height, 'format': "png"}

        uri = pms_url + '/photo/:/transcode?%s' % urlencode(params)

        headers = {'X-Plex-Token': pms_token}

        session = requests.Session()
        try:
            r = session.request("GET", uri, headers=headers)
            r.raise_for_status()
        except Exception:
            return None

        response_status = r.status_code
        response_content = r.content
        response_headers = r.headers
        if response_status in (200, 201):
            return response_content, response_headers['Content-Type']


def get_from_entry(entry):
    blob = None
    content_type = ""
    if "art" in entry:
        pms_image = get_image(entry["art"], 600, 300)
        if pms_image:
            (blob, content_type) = pms_image

    fmt_params = {
        "title": entry["title"],
        "year": entry["year"],
        "audience_rating": entry["audience_rating"],
        "directors": ", ".join(entry["directors"]),
        "actors": ", ".join(entry["actors"]),
        "summary": entry["summary"],
        "tagline": entry["tagline"],
        "genres": ", ".join(entry["genres"])
    }

    return (blob, content_type, fmt_params)


msg_template_html = """
    <b>{title} -({year})- Rating: {audience_rating}</b><br>
    Director(s): {directors}<br>
    Actors: {actors}<br>
    <I>{summary}</I><br>
    {tagline}<br>
    Genre(s): {genres}<br><br>"""

msg_template_plain = """*{title} -({year})- Rating: {audience_rating}*
    Director(s): {directors}
    Actors: {actors}
    {summary}
    {tagline}
    Genre(s): {genres}

"""


class WebServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_post('/notify', self.notify)

    async def run(self):
        if not self.host or not self.port:
            return

        loop = asyncio.get_event_loop()
        runner = web.AppRunner(self.app)
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, host=self.host, port=self.port)
        loop.run_until_complete(site.start())

    async def notify(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            if "genres" in data:
                data["genres"] = data["genres"].split(",")

            if "actors" in data:
                data["actors"] = data["actors"].split(",")

            if "directors" in data:
                data["directors"] = data["directors"].split(",")

            global rooms
            (blob, content_type, fmt_params) = get_from_entry(data)
            await send_entry(blob, content_type, fmt_params, rooms)

        except Exception as exc:
            message = str(exc)
            return web.HTTPBadRequest(body=message)

        return web.Response()


class MatrixModule(BotModule):
    httpd = None
    rooms = dict()
    api_key = None

    def __init__(self, name):
        super().__init__(name)
        self.httpd = WebServer(os.getenv("TAUTULLI_NOTIFIER_ADDR"), os.getenv("TAUTULLI_NOTIFIER_PORT"))

    def matrix_start(self, bot):
        super().matrix_start(bot)
        global global_bot
        global_bot = bot
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.httpd.run())

    def matrix_stop(self, bot):
        super().matrix_stop(bot)

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 3 and args[1] == 'apikey':
            bot.must_be_owner(event)

            self.api_key = args[2]
            bot.save_settings()
            await bot.send_text(room, 'Api key set')
        elif len(args) == 2:
            media_type = args[1]
            if media_type != "movie" and media_type != "show" and media_type != "artist":
                await bot.send_text(room, "media type '%s' provided not valid" % media_type)
                return

            try:
                url = "{}/api/v2?apikey={}&cmd=get_recently_added&count=10".format(os.getenv("TAUTULLI_URL"), self.api_key)
                req = urllib.request.Request(url + "&media_type=" + media_type)
                connection = urllib.request.urlopen(req).read()
                entries = json.loads(connection)
                if "response" not in entries and "data" not in entries["response"] and "recently_added" not in entries["response"]["data"]:
                    await bot.send_text(room, "no recently added for %s" % media_type)
                    return

                for entry in entries["response"]["data"]["recently_added"]:
                    (blob, content_type, fmt_params) = get_from_entry(entry)
                    await send_entry(blob, content_type, fmt_params, {room.room_id: room})

            except urllib.error.HTTPError as err:
                raise ValueError(err.read())
            except Exception as exc:
                message = str(exc)
                await bot.send_text(room, message)
        elif len(args) == 4:
            if args[1] == "add" or args[1] == "remove":
                room_id = args[2]
                encrypted = args[3]
                if args[1] == "add":
                    self.rooms[room_id] = encrypted == "encrypted"
                    await bot.send_text(room, f"Added {room_id} to rooms notification list")
                else:
                    del self.rooms[room_id]
                    await bot.send_text(room, f"Removed {room_id} to rooms notification list")

                bot.save_settings()
                global rooms
                rooms = self.rooms
            else:
                await bot.send_text(room, 'Usage: !tautulli <movie|show|artist>|<add|remove> %room_id% %encrypted%')
        else:
            await bot.send_text(room, 'Usage: !tautulli <movie|show|artist>|<add|remove> %room_id% %encrypted%')

    def get_settings(self):
        data = super().get_settings()
        data["api_key"] = self.api_key
        data["rooms"] = self.rooms
        global rooms
        rooms = self.rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("rooms"):
            self.rooms = data["rooms"]
            global rooms
            rooms = self.rooms
        if data.get("api_key"):
            self.api_key = data["api_key"]

    def help(self):
        return ('Tautulli recently added bot')

