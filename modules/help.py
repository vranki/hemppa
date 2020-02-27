from modules.common.module import BotModule


class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        msg = f'This is Hemppa {bot.version}, a generic Matrix bot. Known commands:\n\n'

        for modulename, moduleobject in bot.modules.items():
            if moduleobject.enabled:
                msg = msg + '!' + modulename
                try:
                    msg = msg + ' - ' + moduleobject.help() + '\n'
                except AttributeError:
                    pass
                msg = msg + '\n'
        msg = msg + "\nMore information at https://github.com/vranki/hemppa"
        await bot.send_text(room, msg)

    def help(self):
        return 'Prints help on commands'
