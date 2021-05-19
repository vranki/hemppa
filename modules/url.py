import re
import shlex
from functools import lru_cache

import httpx
import sys
import traceback
from bs4 import BeautifulSoup
from nio import RoomMessageText

from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    Simple url fetch and spit out title module.

    Everytime a url is seen in a message we do http request to it and try to get a title tag contents to spit out to the room.
    """

    def __init__(self, name):
        super().__init__(name)

        self.bot = None
        self.status = dict()  # room_id -> what to do with urls
        self.type = "m.notice"  # notice or text
        # this will be extended when matrix_start is called
        self.useragent = "Mozilla/5.0 (compatible; Hemppa; +https://github.com/vranki/hemppa/)"

        self.STATUSES = {
            "OFF": "Not spamming this channel",
            "TITLE": "Spamming this channel with titles",
            "DESCRIPTION": "Spamming this channel with descriptions",
            "BOTH": "Spamming this channel with both title and description",
        }
        self.blacklist = [ ]
        self.enabled = False

    def matrix_start(self, bot):
        """
        Register callback for all RoomMessageText events on startup
        """
        super().matrix_start(bot)
        self.bot = bot
        bot.client.add_event_callback(self.text_cb, RoomMessageText)
        # extend the useragent string to contain version and bot name
        self.useragent = f"Mozilla/5.0 (compatible; Hemppa/{self.bot.version}; {self.bot.client.user}; +https://github.com/vranki/hemppa/)"
        self.logger.debug(f"useragent: {self.useragent}")


    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.text_cb)

    def user_agent_for_url(self, url):
        if ('youtube.com' in url) or ('youtu.be' in url) or ('google.com' in url):
            return 'curl/7.64.0'
        return self.useragent

    # Currently not used, but for future needs:
    def cookies_for_url(self, url):
        if ('youtube.com' in url) or ('youtu.be' in url) or ('google.com' in url):
            cookies = httpx.Cookies()
            cookies.set('CONSENT', 'YES', domain='.youtube.com')
            return cookies
#            return {'CONSENT': 'YES', 'Domain': '.youtube.com', 
#                'Path': '/', 'SameSite' : 'None', 'Expires': 'Sun, 10 Jan 2038 07:59:59 GMT', 'Max-Age': '946080000'}
        return {}

    async def text_cb(self, room, event):
        """
        Handle client callbacks for all room text events
        """
        if self.bot.should_ignore_event(event):
            return

        # no content at all?
        if len(event.body) < 1:
            return

        if "content" in event.source:
            # skip edited content to prevent spamming the same thing multiple times
            if "m.new_content" in event.source["content"]:
                self.logger.debug("Skipping edited event to prevent spam")
                return
            # skip reply messages to prevent spam
            if "m.relates_to" in event.source["content"]:
                self.logger.debug("Skipping reply message to prevent spam")
                return

        # are we on in this room?
        status = self.status.get(room.room_id, "OFF")
        if status not in self.STATUSES:
            return
        if status == "OFF":
            return

        try:
            # extract possible urls from message
            urls = re.findall(r"(https?://\S+)", event.body)

            # no urls, nothing to do
            if len(urls) == 0:
                return

            # fetch the urls and if we can see a title spit it out
            for url in urls:
                # fix for #98 a bit ugly, but skip all matrix.to urls
                # those are 99.99% pills and should not
                # spam the channel with matrix.to titles
                if url.startswith("https://matrix.to/#/"):
                    self.logger.debug(f"Skipping matrix.to url (#98): {url}")
                    continue

                url_blacklisted = False
                for blacklisted in self.blacklist:
                    if blacklisted in url:
                        url_blacklisted = True
                if url_blacklisted:
                    self.logger.debug(f"Skipping blacklisted url {url}")
                    continue

                try:
                    title, description = self.get_content_from_url(url)
                except Exception as e:
                    self.logger.warning(f"could not fetch url: {e}")
                    traceback.print_exc(file=sys.stderr)
                    # failed fetching, give up
                    continue

                msg = ""

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

                if msg.strip(): # Evaluates to true on non-empty strings
                    await self.bot.send_text(room, msg, msgtype=self.type, bot_ignore=True)
        except Exception as e:
            self.logger.warning(f"Unexpected error in url module text_cb: {e}")
            traceback.print_exc(file=sys.stderr)

    @lru_cache(maxsize=128)
    def get_content_from_url(self, url):
        """
        Fetch url and try to get the title and description from the response
        """
        title = None
        description = None
        # timeout will still handle network timeouts
        timeout = httpx.Timeout(10.0)
        responsetext = ""  # read our response here
        try:
            self.logger.debug(f"start streaming {url}")
            # stream the response so that we can set a upper limit on how much we want to fetch.
            # as we are using stream the r.text wont be available, save our read data ourself

            # maximum size to read of the response in characters (this prevents us from reading stream forever)
            maxsize = 800000
            headers = {
                'user-agent': self.user_agent_for_url(url)
            }
            # Google may break things anytime so here are some things to try:
            # If needed some day..  'Set-Cookie': "CONSENT=YES; Domain=.youtube.com; Path=/; SameSite=None; Secure; Expires=Sun, 10 Jan 2038 07:59:59 GMT; Max-Age=946080000"
            # cookies = self.cookies_for_url(url)
            # print('cookies', url, cookies)
            # print('headers', headers)
            with httpx.stream("GET", url, timeout=timeout, headers=headers) as r:
                for part in r.iter_text():
                    # self.logger.debug(
                    #     f"reading response stream, limiting in {maxsize} bytes"
                    # )

                    responsetext += part
                    maxsize -= len(part)

                    if maxsize < 0:
                        break

            self.logger.debug(f"end streaming {url}")
        except Exception as e:
            self.logger.warning(f"Failed fetching url {url}. Error: {e}")
            return (title, description)

        if r.status_code != 200:
            self.logger.warning(
                f"Failed fetching url {url}. Status code: {r.status_code}"
            )
            return (title, description)

        # try parse and get the title
        try:
            soup = BeautifulSoup(responsetext, "html.parser")

            if soup.title and len(soup.title.string) > 0:
                title = soup.title.string
            else:
                title_tag = soup.find("meta", attrs={"name": "title"})
                ogtitle = soup.find("meta", property="og:title")
                if title_tag:
                    title = title_tag.get("content", None)
                elif ogtitle:
                    title = ogtitle["content"]
                elif soup.head and soup.head.title:
                    title = soup.head.title.string.strip()
            descr_tag = soup.find("meta", attrs={"name": "description"})
            if descr_tag:
                description = descr_tag.get("content", None)
        except Exception as e:
            self.logger.warning(f"Failed parsing response from url {url}. Error: {e}")
            return (title, description)

        # Title should not contain newlines or tabs
        if title is not None:
            assert isinstance(title, str)
            title = title.replace("\n", "")
            title = title.replace("\t", "")
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
            status = self.STATUSES.get(self.status.get(room.room_id, "OFF")) + f', URL blacklist: {self.blacklist}'
            await bot.send_text(
                room, status
            )
            return

        # set type to notice
        elif len(args) == 1 and args[0] == "notice":
            bot.must_be_owner(event)
            self.type = "m.notice"
            bot.save_settings()
            await bot.send_text(room, "Sending titles as notices from now on.")
            return

        # show status
        elif len(args) == 1 and args[0] == "text":
            bot.must_be_owner(event)
            self.type = "m.text"
            bot.save_settings()
            await bot.send_text(room, "Sending titles as text from now on.")
            return

        # set blacklist
        elif len(args) == 2 and args[0] == "blacklist":
            bot.must_be_owner(event)
            if args[1] == 'clear':
                self.blacklist = []
            else:
                self.blacklist = args[1].split(',')
            bot.save_settings()
            await bot.send_text(room, f"Blacklisted URLs set to {self.blacklist}")
            return

        # invalid command
        await bot.send_text(
            room,
            "Sorry, I did not understand. See README for command list.",
        )

        return

    def get_settings(self):
        data = super().get_settings()
        data["status"] = self.status
        data["type"] = self.type
        data["blacklist"] = self.blacklist
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("status"):
            self.status = data["status"]
        if data.get("type"):
            self.type = data["type"]
        if data.get("blacklist"):
            self.blacklist = data["blacklist"]

    def help(self):
        return "If I see a url in a message I will try to get the title from the page and spit it out"
