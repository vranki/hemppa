import os
import itertools
import shlex
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
        self.enabled = False
        self.access_token = os.getenv("MATRIX_ACCESS_TOKEN")
        self.welcome_settings = dict()

    async def matrix_message(self, bot, room, event):
        bot.must_be_owner(event)
        args = shlex.split(event.body)
        args.pop(0)
        # Message body possibilities:
        #   ["welcome_message", "query_host", "settings"]
        if args[0] == "welcome_message":
            welcome_settings = {"user_query_host": os.getenv("MATRIX_SERVER")}
            users = self.get_server_user_list()
            welcome_settings.update({
                "last_server_user_count": len(users),
                "last_server_users": users,
                "welcome_message": event.body.split("welcome_message", 1)[1] 
            })
            self.welcome_settings = welcome_settings
            bot.save_settings()
            await bot.send_text(room, "Welcome settings configured for server: {settings}".format(settings=welcome_settings))
        elif args[0] == "settings":
            await bot.send_text(room, "Welcome settings for server: {settings}".format(settings=self.welcome_settings))

    def get_settings(self):
        data = super().get_settings()
        data["welcome_settings"] = self.welcome_settings
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("welcome_settings"):
            self.welcome_settings = data["welcome_settings"]

    async def matrix_poll(self, bot, pollcount):
        server_user_delta = self.get_server_user_delta(bot)

        # The first time this bot runs it will detect all users as new, so
        # allow it to one once without taking action.
        if pollcount != 1:
            new_users = server_user_delta.get("recently_added", [])
            await self.welcome_users(
                new_users,
                self.welcome_settings["welcome_message"],
                bot
            )

    def help(self):
        return "Poll for new users on the server and welcome them"

    async def welcome_users(self, user_list, message, bot):
        if len(user_list) > 1:
            print(user_list)
            return
        for user in user_list:
            await bot.send_msg(
                user,
                "Welcome",
                message
            )
        if len(user_list) > 0:
            for owner in bot.owners:
                await bot.send_msg(
                    owner,
                    "Welcome Bot",
                    "Sent a welcome message to new server user(s): {users}".format(
                        users=user_list
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

    def get_server_user_delta(self, bot):
        """
        Get the full user list for the server and return the change in users
        since the last run.
        """
        user_list = self.get_server_user_list()
        user_delta = self.get_user_list_delta(
            user_list,
            self.welcome_settings["last_server_users"]
        )
        self.welcome_settings["last_server_users"] = [u for u in user_list]
        self.welcome_settings["last_server_user_count"] = len(user_list)
        bot.save_settings()
        return user_delta

    def get_server_user_list(self):
        user_data = requests.get(
            self.welcome_settings["user_query_host"] + "/_synapse/admin/v2/users",
            headers={"Authorization": "Bearer {token}".format(
                token=self.access_token
            )}
        )
        user_data_json = user_data.json()
        user_list = [u.get("name") for u in user_data_json.get("users", [])]
        return user_list
