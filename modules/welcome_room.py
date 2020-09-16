import itertools
import shlex
from modules.common.module import BotModule


class MatrixModule(BotModule):
    """
    Detect new users who join the provided room, DM them a welcome message, and
    alert bot owners that a new user has been welcomed.
    """

    def __init__(self, name):
        super().__init__(name)
        self.enabled = False
        self.rooms = dict()

    async def matrix_message(self, bot, room, event):
        bot.must_be_owner(event)
        args = shlex.split(event.body)
        args.pop(0)
        # Message body possibilities:
        #   ["welcome_message", "notify_departure", "settings"]
        if args[0] == "welcome_message":
            users = bot.client.rooms[room.room_id].users
            welcome_settings = {
                "last_room_user_count": len(users),
                "last_room_users": [username for username in users],
                "welcome_message": event.body.split("welcome_message", 1)[1],
                "notify_departure": False
            }
            self.rooms[room.room_id] = welcome_settings
            bot.save_settings()
            await bot.send_text(room, "Welcome settings configured: {settings}".format(settings=welcome_settings))
        elif args[0] == "notify_departure":
            notify_departure = True if args[1] == "True" else False
            self.rooms[room.room_id]["notify_departure"] = notify_departure
            bot.save_settings()
            await bot.send_text(room, "notify_departure set to {setting}".format(setting=notify_departure))
        elif args[0] == "settings":
            await bot.send_text(room, "Welcome settings: {settings}".format(settings=self.rooms[room.room_id]))

    def get_settings(self):
        data = super().get_settings()
        data["rooms"] = self.rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("rooms"):
            self.rooms = data["rooms"]

    async def matrix_poll(self, bot, pollcount):
        for room_id in self.rooms:
            if room_id in bot.client.rooms:
                welcome_parameters = self.rooms[room_id]
                newcomer_room_users = bot.client.rooms[room_id].users
                newcomer_room_user_delta = self.get_user_list_delta(
                    newcomer_room_users,
                    welcome_parameters["last_room_users"]
                )
                self.rooms[room_id]["last_room_user_count"] = len(newcomer_room_users)
                self.rooms[room_id]["last_room_users"] = [u for u in newcomer_room_users]

                if pollcount != 1:
                    new_users = newcomer_room_user_delta.get("recently_added", [])
                    if welcome_parameters["notify_departure"] and \
                            len(newcomer_room_user_delta.get("recently_removed")) > 0:
                        for owner in bot.owners:
                            await bot.send_msg(
                                owner,
                                "Welcome Bot",
                                "User {user_left} left {channel}".format(
                                    user_left=newcomer_room_user_delta.get("recently_removed"),
                                    channel=bot.client.rooms[room_id].display_name
                                )
                            )
                    await self.welcome_users(
                        new_users,
                        welcome_parameters["welcome_message"],
                        bot,
                        bot.client.rooms[room_id].display_name
                    )

    def help(self):
        return "Poll for new users in the room and welcome them"

    async def welcome_users(self, user_list, message, bot, roomname):
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
                    "Sent a welcome message from {channel} to: {users}".format(
                        users=user_list,
                        channel=roomname
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
