from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    This is a substitute for matrix' (element's?) missing user status feature.
    Save a custom (status) message for users and allows to query them.
    """

    def __init__(self, name):
        super().__init__(name)
        self.status = dict()

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) < 1 or args[0] == "help":
            await bot.send_text(room, self.help())
        elif args[0] == "show":
            if len(args) > 1:
                if args[1] in self.status:
                    await bot.send_text(room, f"Status message of {args[1]}: {self.status[args[1]]}")
                else:
                    await bot.send_text(room, f"No status known for {args[1]}")
            else:
                await bot.send_text(room, f"All status messages:\n{self.status}")
        elif args[0] == "clear":
            self.status.pop(event.sender)
            await bot.send_text(room, f"Cleared status of {event.sender}")
        else:
            self.status[event.sender] = " ".join(args)
            bot.save_settings()
            await bot.send_text(room, f"Status message of {event.sender}: {self.status[event.sender]}")

    def get_settings(self):
        data = super().get_settings()
        data["user_status_list"] = self.status
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("user_status_list"):
            self.status = data["user_status_list"]

    def help(self):
        return """
        Store a status message per user and display them.
        Usage:
        !status clear - clear my status
        !status show [user] - show the status of user. If no user is given, show all status messages
        !status help - show this text
        !status [status] - set your status
        """
