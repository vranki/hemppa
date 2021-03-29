from modules.common.module import BotModule


class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):

        args = event.body.split()[1:]
        if len(args) > 0:
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
            msg = f'This is Hemppa {bot.version}, a generic Matrix bot. Known commands:\n\n'

            for modulename, moduleobject in bot.modules.items():
                if moduleobject.enabled:
                    msg = msg + '!' + modulename
                    try:
                        msg = msg + ' - ' + moduleobject.help() + '\n'
                    except AttributeError:
                        pass
            msg = msg + "\nMore information at https://github.com/vranki/hemppa"
        await bot.send_text(room, msg)

    def help(self):
        return 'Prints help on commands'
