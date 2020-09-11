import os
import itertools
from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    Detect new users who join the provided room, DM them a welcome message, and
    alert bot owners that a new user has been welcomed.
    """

    def __init__(self, name):
        super().__init__(name)
        room_id = os.getenv("WELCOME_ROOMID")
        self.room_id = room_id
        self.last_welcome_room_user_count = 0
        self.last_welcome_room_users = []

        # If the provided welcome message is a file path, read the file into
        # the welcome message. Otherwise, use the variable data as the message.
        if os.path.isFile(os.getenv("WELCOME_MESSAGE")):
            with open(os.getenv("WELCOME_MESSAGE"), "r") as file:
                self.welcome_message = file.read()
        else:
            self.welcome_message = os.getenv("WELCOME_MESSAGE")

    async def matrix_message(self, bot, room, event):
        return

    async def matrix_poll(self, bot, pollcount):
        newcomer_room_users = bot.client.rooms[self.room_id].users
        newcomer_room_user_delta = self.get_user_list_delta(
            newcomer_room_users,
            self.last_welcome_room_users
        )
        self.last_welcome_room_user_count = len(newcomer_room_users)
        self.last_welcome_room_users = [u for u in newcomer_room_users]

        if pollcount != 1:
            new_users = newcomer_room_user_delta.get("recently_added", [])
            if os.getenv("WELCOME_ROOM_NOTIFY_DEPARTURE") and \
                    len(newcomer_room_user_delta.get("recently_removed")) > 0:
                for owner in bot.owners:
                    await bot.send_msg(
                        owner,
                        "Welcome Bot",
                        "User {left} left the Newcomers channel".format(
                            left=newcomer_room_user_delta.get(
                                "recently_removed")
                        )
                    )
            await self.welcome_users(new_users, bot)

    def help(self):
        return "Poll for new users in the room and welcome them"

    async def welcome_users(self, user_list, bot):
        for user in user_list:
            await bot.send_msg(
                user,
                "Welcome",
                self.welcome_message
            )
        for owner in bot.owners:
            await bot.send_msg(
                owner,
                "Welcome Bot",
                "Sent a welcome message to: {noobs}".format(
                    noobs=user_list
                )
            )

    def get_user_list_delta(
        self,
        current_user_list,
        previous_user_list
    ):
        recently_added = list(itertools.filterfalse(
            lambda u: u in previous_user_list,
            current_user_list
        ))
        recently_removed = list(itertools.filterfalse(
            lambda u: u in current_user_list,
            previous_user_list
        ))
        total_change = len(recently_added) + len(recently_removed)

        return {
            "total_change": total_change,
            "recently_removed": recently_removed,
            "recently_added": recently_added
        }
