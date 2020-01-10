import re
import shlex
import httpx
from lxml.html.soupparser import fromstring
from nio import RoomMessageText
from functools import lru_cache

class MatrixModule:
    """
    Simple url fetch and spit out title module.

    Everytime a url is seen in a message we do http request to it and try to get a title tag contents to spit out to the room.

    TODO: on/off switch...
    """

    bot = None
    onoff = dict()  # room_id -> true or false

    def matrix_start(self, bot):
        """
        Register callback for all RoomMessageText events on startup
        """
        self.bot = bot
        bot.client.add_event_callback(self.text_cb, RoomMessageText)

    async def text_cb(self, room, event):
        """
        Handle client callbacks for all room text events
        """
        # no content at all?
        if len(event.body) < 1:
            return

        # are we on in this room?
        if self.onoff.get(room.room_id) is not True:
            return

        # extract possible urls from message
        urls = re.findall(r"(https?://\S+)", event.body)

        # no urls, nothing to do
        if len(urls) == 0:
            return

        # fetch the urls and if we can see a title spit it out
        for url in urls:
            title = self.get_title_from_url(url)
            if title is not None:
                await self.bot.send_html(room, f"Title: {title}", f"Title: {title}")

    @lru_cache(maxsize=128)
    def get_title_from_url(self, url):
        """
        Fetch url and try to get the title from the response, returns either the title or None
        """
        try:
            r = httpx.get(url)
        except Exception as e:
            # if it failed then it failed, no point in trying anything fancy
            # this is just a title spitting bot :)
            return None

        if r.status_code != 200:
            return None

        # try parse and get the title
        try:
            elem = fromstring(r.text).find(".//head/title")
        except Exception as e:
            # again, no point in trying anything else
            return None

        if elem is not None:
            return elem.text

        # no bonus
        return None

    async def matrix_message(self, bot, room, event):
        """
        on off switch
        """
        bot.must_be_admin(room, event)

        args = shlex.split(event.body)
        args.pop(0)

        if len(args) == 1:
            if args[0] == "on":
                self.onoff[room.room_id] = True
                bot.save_settings()
                await bot.send_text(
                    room, "Ok, I will spam titles from urls I see on this room."
                )
                return
            if args[0] == "off":
                self.onoff[room.room_id] = False
                bot.save_settings()
                await bot.send_text(
                    room, "Ok, not spamming titles in this room anymore."
                )
                return

            if args[0] == "status":
                if self.onoff.get(room.room_id) is not True:
                    await bot.send_text(
                        room, "Nope, I'm not spamming you with titles."
                    )
                else:
                    await bot.send_text(
                        room, "Yup, spamming you with titles from urls seen."
                    )
                return

        await bot.send_text(
            room,
            "Sorry, I did not understand. I only understand 'on', 'off' and 'status' commands",
        )

        return

    def help(self):
        return "If I see a url in a message I will try to get the title from the page and spit it out"
