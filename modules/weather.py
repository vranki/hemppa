import subprocess
from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        encoding = "utf-8"

        # get weather from ansiweather
        result = subprocess.check_output(["ansiweather", "-a false", "-l", ' '.join(args)])

        await bot.send_text(room, result.decode(encoding))

    def help(self):
        return ('How\'s the weather?')
