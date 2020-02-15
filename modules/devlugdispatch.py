import re

from nio import RoomMessageText

from modules.common.module import BotModule


class MatterMessage:
    def __init__(self, protocol, user, message):
        self.protocol = protocol
        self.username = user
        self.message = message


class MatterBridgeParser:

    def __init__(self):
        self.reg = re.compile(r"\[(.*)\] <(.*)> (.*)")
        self.match = None

    def validate(self, message):
        self.match = self.reg.match(message)
        return self.match is not None

    def parse(self, message):

        if self.validate(message):
            groups = self.match.group(1, 2, 3)
            return MatterMessage(groups[0], groups[1], groups[2])
        else:
            return None


class MatrixModule(BotModule):
    """
    Everytime a matterbridge message is seen, the original message is delegated to the bot for command processing
    """

    def __init__(self, name):
        super().__init__(name)
        self.bot = None
        self.parser = MatterBridgeParser()

    async def matrix_message(self, bot, room, event):

        # todo: add subcommand to add administrators
        # todo: add subcommand to add known matterbridge bot
        # todo: needs a mechanism to hook into admin check of the bot
        pass

    def help(self):
        return "parses matterbridge messages and delegate the parsed message to the bot"

    def matrix_start(self, bot):
        self.bot = bot
        super().matrix_start(bot)
        bot.client.add_event_callback(self.dispatch_cb, RoomMessageText)

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.dispatch_cb)

    async def dispatch_cb(self, room, event):

        # todo: only accept messages from matterbridge bot
        #       like event.sender in self.known_matterbridge_bots

        # no content at all?
        if len(event.body) < 1:
            return

        matter_message = self.parser.parse(event.body)

        if matter_message is None:
            return

        self.logger.info(f"room: {room.name} protocol: {matter_message.protocol} user: {matter_message.username} - dispatch matterbridge message to bot")

        # dispatch. changing the body of the event triggers message_cb of the bot
        event.body = matter_message.message
