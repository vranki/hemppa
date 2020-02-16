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
        self.known_bots = []
        self.bot = None
        self.parser = MatterBridgeParser()

    async def matrix_message(self, bot, room, event):
        bot.must_be_admin(room, event)

        # todo: add subcommand to add administrators
        # todo: add subcommand to add known matterbridge bot
        args = event.body.split()

        if len(args) == 2:
            if args[1] == 'list-bots':
                await self.list_bots(room)
        if len(args) > 2:
            if args[1] == 'add-bot':
                self.add_bot(args[2])
            elif args[1] == 'del-bot':
                self.del_bot(args[2])

        # todo: needs a mechanism to hook into admin check of the bot

    def help(self):
        return "parses matterbridge messages and delegate the parsed message to the bot"

    def matrix_start(self, bot):
        self.bot = bot
        super().matrix_start(bot)
        bot.client.add_event_callback(self.dispatch_cb, RoomMessageText)

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.dispatch_cb)

    def get_settings(self):
        data = super().get_settings()
        data['known_bots'] = self.known_bots
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('known_bots'):
            self.known_bots = data['known_bots']

    async def dispatch_cb(self, room, event):

        if event.sender not in self.known_bots:
            self.logger.debug(f"{event.sender} is not a known bot. skip processing.")
            return

        # no content at all?
        if len(event.body) < 1:
            return

        matter_message = self.parser.parse(event.body)

        if matter_message is None:
            return

        self.logger.info(
            f"room: {room.name} protocol: {matter_message.protocol} user: {matter_message.username} - dispatch matterbridge message to bot")

        # dispatch. changing the body of the event triggers message_cb of the bot
        event.body = matter_message.message

    def add_bot(self, bot_name):
        self.logger.info("Add bot %s to known bots", bot_name)
        self.known_bots.append(bot_name)
        self.bot.save_settings()

    def del_bot(self, bot_name):
        if bot_name in self.known_bots:
            self.logger.info("Delete bot %s from list of known bots", bot_name)
            self.known_bots.remove(bot_name)
            self.bot.save_settings()
        else:
            self.logger.warning("%s not in list of known bots. skip delete.", bot_name)

    async def list_bots(self, room):

        await self.bot.send_text(room, f'Known Matterbridge Bots: {len(self.known_bots)}')
        for bot_name in self.known_bots:
            await self.bot.send_text(room, bot_name)
