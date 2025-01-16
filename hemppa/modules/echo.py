from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        # Echo what they said back
        self.logger.debug(f"room: {room.name} sender: {event.sender} wants an echo")
        await bot.send_text(room, ' '.join(args))

    def help(self):
        return 'Echoes back what user has said'
