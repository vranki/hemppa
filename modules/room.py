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

        if args[0] == 'servers':
            await MatrixModule.servers_in_room(bot, room)

    @staticmethod
    async def servers_in_room(bot, room: nio.MatrixRoom):
        servers_in_room = "Servers in room:\n"
        count = 0
        response = await bot.client.joined_members(room.room_id)

        if isinstance(response, nio.JoinedMembersError):
            raise response
        else:
            for member in response.members:
                assert isinstance(member, nio.RoomMember)
                server = member.user_id.split(':')[1]
                if server not in servers_in_room:
                    count += 1
                    servers_in_room += f" - {server}\n"
            servers_in_room = f"({count}) {servers_in_room}"
            await bot.send_text(room, servers_in_room)