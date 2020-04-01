from modules.common.module import BotModule
import nio


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)

    def help(self):
        pass

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

