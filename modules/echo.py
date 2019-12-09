class MatrixModule:
    def matrix_start(self, bot):
        print("Echo started.")

    def matrix_stop(self, bot):
        print("Echo stopped")

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        # Echo what they said back
        await bot.send_text(room, ' '.join(args))

    def help(self):
        return('Echoes back what user has said')
