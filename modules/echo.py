class MatrixModule:
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        # Echo what they said back
        await bot.send_text(room, ' '.join(args))

    def help(self):
        return('Echoes back what user has said')
