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
                msg = ['Aliases:']
                inverted = dict()
                for k, v in bot.module_aliases.items():
                    inverted.setdefault(v, list()).append(k)
                self.logger.debug(f"room: {room.name} sender: {event.sender} wants to list aliases")
                for k, v in inverted.items():
                    v = ', '.join(v)
                    msg.append(f'- {k} = {v}')
                await bot.send_text(room, '\n'.join(msg))

            elif args.pop(0) == 'help':
                await bot.send_text(room, self.long_help(bot=bot, event=event))

    def help(self):
        return 'Manage command aliases'

    def long_help(self, bot=None, event=None, **kwargs):
        text = self.help() + (
                '\n- "!alias (list|ls)": list defined aliases'
                '\n- "!alias help": show this help')
        if bot and event and bot.is_owner(event):
            text += ('\n- "!alias (remove|rm) [name]": remove an alias'
                     '\n- "!alias add [name] [command]": add an alias for [command]')
        return text
