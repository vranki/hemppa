from modules.common.module import BotModule
import nio


class MatrixModule(BotModule):
    """ This module is for interacting with the room that the commands are being executed on.
    Commands:
        servers: Lists the servers in the room
        joined: Responds with the joined members count
        banned: Lists the banned users and their provided reason
        kicked: Lists the kicked users and their provided reason
        state: Gets a state event with given event type and optional state key

    Author:
        Dylan Hackworth <dhpf@pm.me>
    """
    def __init__(self, name):
        super().__init__(name)

    def help(self):
        return "Commands for interacting with the current room "

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        command = args[0]

        if command == 'servers':
            await MatrixModule.servers_in_room(bot, room)
        elif command == 'joined':
            await MatrixModule.joined_members(bot, room)
        elif command == 'banned':
            await MatrixModule.banned_members(bot, room)
        elif command == 'kicked':
            await MatrixModule.kicked_members(bot, room)
        elif command == 'state':
            await MatrixModule.get_state_event(bot, room, args)

    @staticmethod
    async def servers_in_room(bot, room: nio.MatrixRoom):
        """ This command lists all the servers in the room

        This function iterates through all the joined members (m.room.member state events), grabs the member's domain
        and adds it to the "Servers in room" string then it inserts the number of servers at the beginning of the string
        and then sends it to the room that the command was executed.

        :param bot: modules.Bot
        :param room: nio.MatrixRoom
        :return: None
        """
        servers_in_room = "Servers in room:\n"
        server_count = 0
        response = await bot.client.joined_members(room.room_id)

        # If the the joined_members successfully got all the joined room members then ...
        if isinstance(response, nio.JoinedMembersResponse):
            # Iterate through all the joined members
            for member in response.members:
                # Grab their homeserver
                server = member.user_id.split(':')[1]
                # if this member's homeserver isn't on the list
                if server not in servers_in_room:
                    # Then add to the counter
                    server_count += 1
                    # Append to the servers string
                    servers_in_room += f" - {server}\n"
            # Insert the server counter at the begging of the servers string
            servers_in_room = f"({server_count}) {servers_in_room}"
            # Send it back to the command executor
            await bot.send_text(room, servers_in_room)
        # Else if the joined_members failed to get the joined room members
        else:
            # Then raise the error and the bot module will handle everything else
            raise response

    @staticmethod
    async def joined_members(bot, room: nio.MatrixRoom):
        """ This commands provides a count of how many joined members there are

        :param bot: modules.bot
        :param room: nio.MatrixRoom
        :return: None
        """
        await bot.send_text(room, f"Member count: {room.member_count}")

    @staticmethod
    async def banned_members(bot, room: nio.MatrixRoom):
        """ This command lists all the banned members along with the provided reason

        This function iterates through the room's m.room.member state events, checks if they're banned and if they're
        banned then add to the banned members string as well as the reason if it's defined. Then it is sent back to the
        command executor

        :param bot: modules.bot
        :param room: nio.MatrixRoom
        :return: None
        """
        banned_members = "Banned members:\n"
        banned_members_count = 0
        res = await bot.client.room_get_state(room.room_id)

        # If room_get_state successfully got the state events in the room then ...
        if isinstance(res, nio.RoomGetStateResponse):
            # Iterate through all the state events
            for state in res.events:
                # Filter out the m.room.member state events
                if state["type"] == "m.room.member":
                    content = state["content"]
                    # Check if the member was banned (ban)
                    if content["membership"] == "ban":
                        # Get the member's name
                        name = state["state_key"]
                        # The reason if it's defined otherwise reason = "No reason"
                        reason = content.get("reason") or "No reason"
                        # Add to the string of banned members
                        banned_members += f" - {name}: \"{reason}\"\n"
                        # Added to the banned members counter
                        banned_members_count += 1
            # Insert the banned members counter to the beginning of the banned_members string
            banned_members = f"({banned_members_count}) {banned_members}"
            # Send it back to the command executor
            await bot.send_text(room, banned_members)
        # Otherwise res is a typeof error so
        else:
            # Raise the error and the bot module will handle everything else
            raise res

    @staticmethod
    async def kicked_members(bot, room: nio.MatrixRoom):
        """ This command lists all the kicked members along with the provided reason

        This function iterates through the room's m.room.member state events, checks if they have "leave" as their
        membership and if there is a reason defined, otherwise if there is no reason then there is no way to tell if
        they've been kicked

        :param bot: modules.bot
        :param room: nio.MatrixRoom
        :return: None
        """
        kicked_members = "Kicked members:\n"
        kicked_members_count = 0
        res = await bot.client.room_get_state(room.room_id)

        # If room_get_state successfully got the state events in the room then ...
        if isinstance(res, nio.RoomGetStateResponse):
            # Iterate through all the state events
            for state in res.events:
                # Filter out the m.room.member state events
                if state["type"] == "m.room.member":
                    content = state["content"]
                    # Check if the user is left from the room
                    if content["membership"] == "leave":
                        # Check if the reason is defined
                        if content.get("reason") is not None:
                            # Get the member's name
                            name = state["state_key"]
                            # Get the kick reason
                            reason = content["reason"]
                            # Add to the string of kicked members
                            kicked_members += f" - {name}: \"{reason}\"\n"
                            # Added to the kicked members counter
                            kicked_members_count += 1
            # Insert the kicked members counter to the beginning of the banned_members string
            kicked_members = f"({kicked_members_count}) {kicked_members}"
            # Send it back to the command executor
            await bot.send_text(room, kicked_members)
        # Otherwise res is a typeof error so
        else:
            # Raise the error and the bot module will handle everything else
            raise res

    @staticmethod
    async def get_state_event(bot, room, args):
        """ This command gets a state event with given event type and optional state key

        This function intakes at least one argument representing the event type being grabbed from the room and an
        another optional argument representing the state key, otherwise a blank state key will be provided to the
        Matrix server.

        :param bot: modules.bot
        :param room: nio.MatrixRoom
        :param args: str[]
        :return: None

        Examples of args:
            ["state", "m.room.name"]
            ["state", "m.room.member", "@example:example.org"]
        """
        # The user's provided event type
        user_state_event_type = args[1]
        # The user's optional state key (otherwise blank if None)
        user_state_key = args[2] if len(args) > 2 else ""
        res = await bot.client.room_get_state_event(room.room_id, user_state_event_type, user_state_key)

        # If the state event was successfully gotten then ...
        if isinstance(res, nio.RoomGetStateEventResponse):
            # Stringify the event's content
            result = str(res.content)
            # Respond to the command executor
            await bot.send_text(room, result)
        # Otherwise res is an error
        else:
            # Raise the error and the bot module will handle the rest
            raise res
