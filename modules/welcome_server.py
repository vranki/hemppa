import os
import itertools
import requests
from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    Detect new users who join the server, DM them a welcome message, and alert
    bot owners that a new user has been welcomed.

    Note: This module will only work if the bot is a server admin. This
    privilege level has risks.
    """

    def __init__(self, name):
        super().__init__(name)
        self.access_token = os.getenv("MATRIX_ACCESS_TOKEN")
        self.user_query_url = os.getenv("MATRIX_SERVER") + "/_synapse/admin/v2/users"
        self.last_server_user_count = 0
        self.last_server_users = []

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
        server_user_delta = self.get_server_user_delta()

        # The first time this bot runs it will detect all users as new, so
        # allow it to one once without taking action.
        if pollcount != 1:
            new_users = [u.get("name") for u in server_user_delta.get(
                "recently_added", [])]
            await self.welcome_users(new_users, bot)

    def help(self):
        return "Poll for new users on the server and welcome them"

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
                "Sent a welcome message to: {new_users}".format(
                    new_users=user_list
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

    def get_server_user_delta(self):
        """
        Get the full user list for the server and return the change in users
        since the last run.
        """
        user_data = requests.get(
            self.user_query_url,
            headers={"Authorization": "Bearer {token}".format(
                token=self.access_token
            )}
        )
        user_data_json = user_data.json()
        user_list = user_data_json.get("users", [])
        user_delta = self.get_user_list_delta(
            user_list,
            self.last_server_users
        )
        self.last_server_users = [u for u in user_list]
        self.last_server_user_count = user_data_json.get("total")
        return user_delta
