import urllib.request
import urllib.parse
import urllib.error
import datetime
import pytz
import os
import sys
import json

import importlib
from importlib import reload

from nio import MatrixRoom

from aiohttp import web
import asyncio
import nest_asyncio
nest_asyncio.apply()

from modules.common.module import BotModule

tautulli_path = os.getenv("TAUTULLI_PATH")

def load_tzlocal():
    try:
        global tautulli_path

        sys.path.insert(0, tautulli_path)
        sys.path.insert(0, "{}/lib".format(tautulli_path))
        module = importlib.import_module("tzlocal")
        module = reload(module)
        return module
    except ModuleNotFoundError:
        return None

def load_tautulli():
    try:
        global tautulli_path

        sys.path.insert(0, tautulli_path)
        sys.path.insert(0, "{}/lib".format(tautulli_path))
        module = importlib.import_module("plexpy")
        module = reload(module)
        return module
    except ModuleNotFoundError:
        return None

plexpy = load_tautulli()
tzlocal = load_tzlocal()

send_entry_lock = asyncio.Lock()

async def send_entry(bot, room, entry):
    global send_entry_lock
    async with send_entry_lock:
        if "art" in entry:
            global plexpy
            if plexpy:
                pms = plexpy.pmsconnect.PmsConnect()
                pms_image = pms.get_image(entry["art"], 600, 300)
                if pms_image:
                    (blob, content_type) = pms_image
                    await bot.upload_and_send_image(room, blob, "", True, content_type)

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

        await bot.send_html(room,
            msg_template_html.format(**fmt_params),
            msg_template_plain.format(**fmt_params))

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
    bot = None
    rooms = dict()

    def __init__(self, host, port):
        self.app = web.Application()
        self.host = host
        self.port = port
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

            for room_id in self.rooms:
                room = MatrixRoom(room_id=room_id, own_user_id=os.getenv("BOT_OWNERS"), encrypted=self.rooms[room_id])
                await send_entry(self.bot, room, data)

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
        global plexpy
        if plexpy:
            global tautulli_path
            plexpy.FULL_PATH = "{}/Tautulli.py".format(tautulli_path)
            plexpy.PROG_DIR = os.path.dirname(plexpy.FULL_PATH)
            plexpy.DATA_DIR = tautulli_path
            plexpy.DB_FILE = os.path.join(plexpy.DATA_DIR, plexpy.database.FILENAME)

            try:
                plexpy.SYS_TIMEZONE = tzlocal.get_localzone()
            except (pytz.UnknownTimeZoneError, LookupError, ValueError) as e:
                plexpy.SYS_TIMEZONE = pytz.UTC

            plexpy.SYS_UTC_OFFSET = datetime.datetime.now(plexpy.SYS_TIMEZONE).strftime('%z')
            plexpy.initialize("{}/config.ini".format(tautulli_path))

        self.httpd = WebServer(os.getenv("TAUTULLI_NOTIFIER_ADDR"), os.getenv("TAUTULLI_NOTIFIER_PORT"))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.httpd.run())

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.httpd.bot = bot

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
                req = urllib.request.Request(url+"&media_type="+media_type)
                connection = urllib.request.urlopen(req).read()
                entries = json.loads(connection)
                if "response" not in entries and "data" not in entries["response"] and "recently_added" not in entries["response"]["data"]:
                    await bot.send_text(room, "no recently added for %s" % media_type)
                    return

                for entry in entries["response"]["data"]["recently_added"]:
                    await send_entry(bot, room, entry) 

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
                self.httpd.rooms = self.rooms
            else:
                await bot.send_text(room, 'Usage: !tautulli <movie|show|artist>|<add|remove> %room_id% %encrypted%')
        else:
            await bot.send_text(room, 'Usage: !tautulli <movie|show|artist>|<add|remove> %room_id% %encrypted%')

    def get_settings(self):
        data = super().get_settings()
        data["api_key"] = self.api_key
        data["rooms"] = self.rooms
        self.httpd.rooms = self.rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("rooms"):
            self.rooms = data["rooms"]
            self.httpd.rooms = self.rooms
        if data.get("api_key"):
            self.api_key = data["api_key"]

    def help(self):
        return ('Tautulli recently added bot')
