from modules.common.module import BotModule


class MatrixModule(BotModule):

    def __init__(self, name):
        super().__init__(name)
        self.msg_users = False

    def get_settings(self):
        data = super().get_settings()
        data['msg_users'] = self.msg_users
        data['info'] = self.info
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('msg_users'):
            self.msg_users = data['msg_users']
        self.info = data.get('info') or "\nMore information at https://github.com/vranki/hemppa"

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, ['sethelp'])

    async def matrix_message(self, bot, room, event):

        args = event.body.split(None, 2)
        cmd = args.pop(0)
        if cmd == '!sethelp':
            bot.must_be_owner(event)
            if args[0].lower() in ['msg_users', 'msg-users', 'msg']:
                if args[1].lower() in ['true', '1', 'yes', 'y']:
                    self.msg_users = True
                    msg = '!help will now message users instead of posting to the room'
                else:
                    self.msg_users = False
                    msg = '!help will now post to the room instead of messaging users'
                bot.save_settings()
            elif args[0].lower() in ['info']:
                self.info = args[1] or "More information at https://github.com/vranki/hemppa"
                msg = '!help info string set'
                bot.save_settings()
            else:
                await bot.send_text(room, f'Not a !help setting: {args[0]}')
            return

        elif len(args) == 1:
            msg = ''
            modulename = args.pop(0)
            moduleobject = bot.modules.get(modulename)
            if not moduleobject.enabled:
                msg += f'{modulename} is disabled\n'
            try:
                msg += moduleobject.long_help(bot=bot, room=room, event=event, args=args)
            except AttributeError:
                msg += f'{modulename} has no help'

        else:
            msg = f'This is Hemppa {bot.version}, a generic Matrix bot. Known commands:\n'

            for modulename, moduleobject in bot.modules.items():
                if moduleobject.enabled:
                    msg = msg + '- !' + modulename
                    try:
                        msg = msg + ': ' + moduleobject.help() + '\n'
                    except AttributeError:
                        pass
            msg = msg + '\n' + self.info
        if self.msg_users:
            await bot.send_msg(event.sender, f'Chat with {bot.matrix_user}', msg)
        else:
            await bot.send_text(room, msg)

    def help(self):
        return 'Prints help on commands'
