import time


class MatrixModule:
    def matrix_start(self, bot):
        self.starttime = time.time()

    async def matrix_message(self, bot, room, event):
        await bot.send_text(room, 'Uptime: ' + str(int(time.time() - self.starttime)) + ' seconds.')

    def matrix_stop(self, bot):
        pass

    def help(self):
        return('Tells how many seconds the bot has been up.')
