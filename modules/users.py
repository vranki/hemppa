from modules.common.module import BotModule
import fnmatch

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.classes = dict() # classname <-> pattern

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        if len(args) == 1:
            if args[0] == 'stats' or args[0] == 'roomstats':
                stats = dict()
                for name, pattern in self.classes.items():
                    stats[name] = 0
                if args[0] == 'stats':
                    allusers = self.get_users(bot)
                else:
                    allusers = self.get_users(bot, room.room_id)
                total = len(allusers)
                if total == 0:
                    await bot.send_text(room, "I don't see any users. How did this happen?")
                    return

                matched = 0
                for user in allusers:
                    for name, pattern in self.classes.items():
                        match = fnmatch.fnmatch(user, pattern)
                        if match:
                            stats[name] = stats[name] + 1
                            matched = matched + 1
                
                stats['Matrix'] = total - matched
                stats = dict(sorted(stats.items(), key=lambda item: item[1], reverse=True))

                if args[0] == 'stats':
                    reply = f'I am seeing total {len(allusers)} users in {len(self.bot.client.rooms)} rooms:\n'
                else:
                    reply = f'I am seeing {len(allusers)} users in this room:\n'
                for name in stats:
                    reply = reply + f' - {name}: {stats[name]} ({round(stats[name] / total * 100, 2)}%)\n'
                await bot.send_text(room, reply)
                return
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
            if args[0] == 'classify':
                if args[1] == 'list':
                    await bot.send_text(room, f'Classes in use: {self.classes}.')
                    return
        elif len(args) == 4:
            if args[0] == 'classify':
                if args[1] == 'add':
                    bot.must_be_owner(event)
                    name = args[2]
                    pattern = args[3]
                    self.classes[name] = pattern
                    await bot.send_text(room, f'Added class {name} pattern {pattern}.')
                    bot.save_settings()
                    return
        elif len(args) == 3:
            if args[0] == 'classify':
                if args[1] == 'del':
                    bot.must_be_owner(event)
                    name = args[2]
                    del self.classes[name]
                    await bot.send_text(room, f'Deleted class {name}.')
                    bot.save_settings()
                    return

        await bot.send_text(room, 'Unknown command - please see readme')

    def get_users(self, bot, roomid=None):
        allusers = []
        for croomid in self.bot.client.rooms:
            if roomid and (roomid != croomid):
                break
            try:
                users = self.bot.client.rooms[croomid].users
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Couldn't get user list in room with id {croomid}, skipping: {repr(e)}")
                continue
            for user in users:
                allusers.append(user)
        allusers = list(dict.fromkeys(allusers)) # Deduplicate
        return allusers

    def search_users(self, bot, pattern):
        allusers = self.get_users(self, bot)
        return fnmatch.filter(allusers, pattern)

    def help(self):
        return 'User management tools'

    def get_settings(self):
        data = super().get_settings()
        data["classes"] = self.classes
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("classes"):
            self.classes = data["classes"]

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot