import re
import shlex
from functools import lru_cache

import httpx
from bs4 import BeautifulSoup
from nio import RoomMessageText

from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    Simple url fetch and spit out title module.

    Everytime a url is seen in a message we do http request to it and try to get a title tag contents to spit out to the room.
    """

    bot = None
    status = dict()  # room_id -> what to do with urls

    STATUSES = {
        "OFF": "Not spamming this channel",
        "TITLE": "Spamming this channel with titles",
        "DESCRIPTION": "Spamming this channel with descriptions",
        "BOTH": "Spamming this channel with both title and description",
    }

    def matrix_start(self, bot):
        """
        Register callback for all RoomMessageText events on startup
        """
        super().matrix_start(bot)
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
        status = self.status.get(room.room_id, "OFF")
        if status not in self.STATUSES:
            return
        if status == "OFF":
            return

        # extract possible urls from message
        urls = re.findall(r"(https?://\S+)", event.body)

        # no urls, nothing to do
        if len(urls) == 0:
            return

        # fetch the urls and if we can see a title spit it out
        for url in urls:
            try:
                title, description = self.get_content_from_url(url)
            except Exception:
                # failed fetching, give up
                continue

            msg = None

            if status == "TITLE" and title is not None:
                msg = f"Title: {title}"
            elif status == "DESCRIPTION" and description is not None:
                msg = f"Description: {description}"

            elif status == "BOTH" and title is not None and description is not None:
                msg = f"Title: {title}\nDescription: {description}"

            elif status == "BOTH" and title is not None:
                msg = f"Title: {title}"
            elif status == "BOTH" and description is not None:
                msg = f"Description: {description}"

            if msg is not None:
                await self.bot.send_text(room, msg)

    @lru_cache(maxsize=128)
    def get_content_from_url(self, url):
        """
        Fetch url and try to get the title and description from the response
        """
        title = None
        description = None

        try:
            r = httpx.get(url)
        except Exception as e:
            self.logger.error(f"Failed fetching url {url}. Error: {e}")
            return (title, description)

        if r.status_code != 200:
            self.logger.info(f"Failed fetching url {url}. Status code: {r.status_code}")
            return (title, description)

        # try parse and get the title
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string
            descr_tag = soup.find("meta", attrs={"name": "description"})
            if descr_tag:
                description = descr_tag.get("content", None)
        except Exception as e:
            self.logger.error(f"Failed parsing response from url {url}. Error: {e}")
            return (title, description)

        return (title, description)

    async def matrix_message(self, bot, room, event):
        """
        commands for setting what to do in this channel
        """
        bot.must_be_admin(room, event)

        args = shlex.split(event.body)
        args.pop(0)

        # save the new status
        if len(args) == 1 and self.STATUSES.get(args[0].upper()) is not None:
            self.status[room.room_id] = args[0].upper()
            bot.save_settings()
            await bot.send_text(
                room, f"Ok, {self.STATUSES.get(self.status[room.room_id])}"
            )
            return

        # show status
        elif len(args) == 1 and args[0] == "status":
            await bot.send_text(
                room, self.STATUSES.get(self.status.get(room.room_id, "OFF"))
            )
            return

        # invalid command
        await bot.send_text(
            room,
            "Sorry, I did not understand. I only understand 'title', 'description', 'both' and 'status' commands",
        )

        return

    def get_settings(self):
        data = super().get_settings()
        data['status'] = self.status
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("status"):
            self.status = data["status"]

    def help(self):
        return "If I see a url in a message I will try to get the title from the page and spit it out"

    def dump(self, obj):
        for attr in dir(obj):
            self.logger.info("obj.%s = %r", attr, getattr(obj, attr))
