from modules.common.module import BotModule
import fnmatch

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        if len(args) == 2:
            if args[0] == 'list':
                bot.must_be_owner(event)
                users = self.search_users(bot, args[1])
                if len(users):
                    await bot.send_text(room, ' '.join(users))
                else:
                    await bot.send_text(room, 'No matching users found!')
                return
            if args[0] == 'kick':
                bot.must_be_admin(room, event)
                users = self.search_users(bot, args[1])
                if len(users):
                    for user in users:
                        self.logger.debug(f"Kicking {user} from {room.room_id} as requested by {event.sender}")
                        await bot.client.room_kick(room.room_id, user)
                else:
                    await bot.send_text(room, 'No matching users found!')
                return
        await bot.send_text(room, 'Unknown command - please see readme')

    def search_users(self, bot, pattern):
        allusers = []
        for croomid in bot.client.rooms:
            try:
                users = bot.client.rooms[croomid].users
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Couldn't get user list in room with id {croomid}, skipping: {repr(e)}")
                continue
            for user in users:
                allusers.append(user)
        allusers = list(dict.fromkeys(allusers)) # Deduplicate
        return fnmatch.filter(allusers, pattern)

    def help(self):
        return 'User management tools'
