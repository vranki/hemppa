import html
import time
import markdown

from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    This is a substitute for matrix' (element's?) missing user status feature.
    Save a custom (status) message for users and allows to query them.
    """

    def __init__(self, name):
        super().__init__(name)
        self.status = dict()  # the values are tuples of (status_message, created_at_timestamp)
        self.ttl = 60 * 60 * 24 * 7  # Time to live in seconds. Defaults to one week. Older messages are purged.

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) < 1 or args[0] == "help":
            await self.command_help(bot, room)
        elif args[0] == "show":
            if len(args) > 1:
                await self.send_status(bot=bot, room=room, user=args[1])
            else:
                await self.send_status(bot=bot, room=room)
        elif args[0] == "clear":
            if len(args) > 1 and args[1] == "all":
                bot.must_be_admin(room, event)
                self.status = dict()
            else:
                if (event.sender in self.status.keys()):
                    self.status.pop(event.sender)
                bot.save_settings()
                await bot.send_text(room, f"Cleared status of {event.sender}")
        elif args[0] == "ttl":
            if len(args) > 1:
                bot.must_be_admin(room, event)
                self.ttl = float(args[1])
                bot.save_settings()
            await bot.send_text(room, f"Current status TTL is {self.ttl} seconds = {self.ttl / 60.0 / 60.0 / 24.0} days")
        else:
            self.status[event.sender] = (" ".join(args), time.time())
            bot.save_settings()
            await self.send_status(bot=bot, room=room, user=event.sender)

    def drop_old_messages(self):
        "Drop all messages which are older than the current TTL."
        self.logger.debug(f"status messages: {self.status}")
        dropping = [x for x in self.status.keys() if type(self.status[x]) is str or len(self.status[x]) < 2 or time.time() > self.status[x][1] + self.ttl]
        for x in dropping:
            self.logger.info(f"Dropping old status message {self.status[x]} for user {x}. (now = {time.time()}, ttl = {self.ttl})")
            self.status.pop(x)

    async def send_status(self, bot, room, user=None):
        self.drop_old_messages()
        if user:
            if user in self.status:
                await bot.send_html(room, f"<b>{html.escape(user)}:</b> {markdown.markdown(self.status[user][0])}", f"Status message of {user}: {self.status[user][0]}")
            else:
                await bot.send_text(room, f"No status known for {user}")
        else:
            await bot.send_html(room, "<b>All status messages:</b><br/><ul><li>" +
                                "</li><li>".join([f"<b>{html.escape(key)}:</b> {markdown.markdown(value[0])}" for key, value in self.status.items()]) +
                                "</li></ul>", f"All status messages:\n{self.status}")

    def get_settings(self):
        data = super().get_settings()
        data["user_status_list"] = self.status
        data["user_status_list_ttl"] = self.ttl
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("user_status_list"):
            self.status = data["user_status_list"]
        if data.get("user_status_list_ttl"):
            self.ttl = data["user_status_list_ttl"]

    async def command_help(self, bot, room):
        msg = """
        Store a status message per user and display them.
        Usage:
        !status clear - clear my status
        !status clear all - clear all status messages (admin only)
        !status show [user] - show the status of user. If no user is given, show all status messages
        !status ttl [ttl] Show the current ttl for status messages. If a new ttl is given, set the ttl (must be admin)
        !status help - show this text
        !status [status] - set your status
        """
        await bot.send_html(room, msg, "Status module help")

    def help(self):
        return "Save a custom (status) message for users and allows to query them."
