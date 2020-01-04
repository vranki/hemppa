import urllib.request


class MatrixModule:
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2:
            if args[1]=='quit':
                bot.must_be_admin(room, event)
                await bot.send_text(room, f'Quitting, as requested')
                print(f'{event.sender} commanded bot to quit, so quitting..')
                bot.bot_task.cancel()
            elif args[1]=='version':
                await bot.send_text(room, f'Hemppa version {bot.version} - https://github.com/vranki/hemppa')
        else:
            await bot.send_text(room, 'Unknown command, sorry.')

    def help(self):
        return('Bot management commands')
