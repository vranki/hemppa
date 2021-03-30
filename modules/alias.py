from modules.common.module import BotModule
import random

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.aliases = dict()

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('aliases'):
            self.aliases = data['aliases']

    def get_settings(self):
        data = super().get_settings()
        data['aliases'] = self.aliases
        return data

    def matrix_start(self, bot):
        super().matrix_start(bot)
        bot.module_aliases.update(self.aliases)

    async def matrix_message(self, bot, room, event):

        args = event.body.split()
        args.pop(0)

        if len(args) == 3:
            if args.pop(0) == 'add':
                bot.must_be_owner(event)
                self.logger.debug(f"room: {room.name} sender: {event.sender} wants to add an alias")

                bot.module_aliases.update({args[0]: args[1]})
                self.aliases.update({args[0]: args[1]})
                bot.save_settings()
                await bot.send_text(room, f'Aliased !{args[0]} to !{args[1]}')

        elif len(args) == 2:
            if args.pop(0) in ['rm', 'remove']:
                bot.must_be_owner(event)
                self.logger.debug(f"room: {room.name} sender: {event.sender} wants to remove an alias")

                old = bot.module_aliases.pop(args[0])
                self.aliases.pop(args[0])
                bot.save_settings()
                await bot.send_text(room, f'Removed alias !{args[0]}')

        elif len(args) == 1:
            if args.pop(0) in ['ls', 'list']:
                self.logger.debug(f"room: {room.name} sender: {event.sender} wants to list aliases")
                msg = '\n'.join([ f'- {key} => {val}' for key, val in bot.module_aliases.items() ])
                await bot.send_text(room, 'Aliases:\n' + msg)

    def help(self):
        return 'Alias a command'
