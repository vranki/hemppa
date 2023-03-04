import re

from modules.common.module import BotModule
from nio import RoomMessageText


# This module reads matrix messages and converts twitter.com links to nitter.nl
# Module will only target messages that contain only the twitter link
# Additionally module will target only profile links or post links, query parameters are removed
class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.regex = re.compile(r'https://twitter.com/([^?]*)')
        self.bot = None
        self.enabled_rooms = []

    def matrix_start(self, bot):
        """
        Register callback for all RoomMessageText events on startup
        """
        super().matrix_start(bot)
        self.bot = bot
        bot.client.add_event_callback(self.text_cb, RoomMessageText)

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.text_cb)

    async def text_cb(self, room, event):
        """
        Handle client callbacks for all room text events
        """
        if room.room_id not in self.enabled_rooms:
            return

        if self.bot.should_ignore_event(event):
            return

        # no content at all?
        if len(event.body) < 1:
            return

        if event.body.startswith('!'):
            return

        if len(event.body.split()) <= 1:
            if event.body.startswith('https://twitter.com/'):
                for link in self.regex.findall(event.body):
                    await self.bot.send_text(room, f'https://nitter.net/{link}')
                return

    async def matrix_message(self, bot, room, event):
        """
        Required for initialization of the module
        """
        args = event.body.split()
        args.pop(0)
        if len(args) == 0:
            await bot.send_text(room, 'Usage: !twitter <enable|disable>')
            return
        if len(args) == 1:
            if args[0] == 'enable':
                bot.must_be_admin(room, event)
                self.enabled_rooms.append(room.room_id)
                self.enabled_rooms = list(dict.fromkeys(self.enabled_rooms))  # Deduplicate
                await bot.send_text(room, "Ok, enabling conversion of twitter links to nitter links here")
                bot.save_settings()
                return
            if args[0] == 'disable':
                bot.must_be_admin(room, event)
                self.enabled_rooms.remove(room.room_id)
                await bot.send_text(room, "Ok, disabling conversion of twitter links to nitter links here")
                bot.save_settings()
                return

    def help(self):
        return 'Converts Twitter links to nitter links.'

    def get_settings(self):
        data = super().get_settings()
        data["enabled_rooms"] = self.enabled_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("enabled_rooms"):
            self.enabled_rooms = data["enabled_rooms"]
