from datetime import datetime
from modules.common.module import BotModule


class MatrixModule(BotModule):

    def matrix_start(self, bot):
        self.starttime = datetime.now()
        
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2:
            if args[1] == 'quit':
                await self.quit(bot, room, event)
            elif args[1] == 'version':
                await self.version(bot, room)
            elif args[1] == 'reload':
                await self.reload(bot, room, event)
            elif args[1] == 'status':
                await self.status(bot, room)
            elif args[1] == 'stats':
                await self.stats(bot, room)
            elif args[1] == 'leave':
                await self.leave(bot, room, event)

        else:
            await bot.send_text(room, 'Unknown command, sorry.')

    async def leave(self, bot, room, event):
        bot.must_be_admin(room, event)
        print(f'{event.sender} asked bot to leave room {room.room_id}')
        await bot.send_text(room, f'By your command.')
        await bot.client.room_leave(room.room_id)

    async def stats(self, bot, room):
        roomcount = len(bot.client.rooms)
        usercount = 0
        homeservers = dict()
        for croomid in bot.client.rooms:
            roomobj = bot.client.rooms[croomid]
            usercount = usercount + len(roomobj.users)
            for user in roomobj.users:
                hs = user.split(':')[1]
                if homeservers.get(hs):
                    homeservers[hs] = homeservers[hs] + 1
                else:
                    homeservers[hs] = 1
        homeservers = sorted(homeservers.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
        if len(homeservers) > 10:
            homeservers = homeservers[0:10]
        await bot.send_text(room,
                            f'I\'m seeing {usercount} users in {roomcount} rooms. Top ten homeservers: {homeservers}')

    async def status(self, bot, room):
        uptime = datetime.now() - self.starttime
        await bot.send_text(room,
                            f'Uptime {uptime} - system time is {datetime.now()} - loaded {len(bot.modules)} modules.')

    async def reload(self, bot, room, event):
        bot.must_be_admin(room, event)
        await bot.send_text(room, f'Reloading modules..')
        bot.stop()
        bot.reload_modules()
        bot.start()

    async def version(self, bot, room):
        await bot.send_text(room, f'Hemppa version {bot.version} - https://github.com/vranki/hemppa')

    async def quit(self, bot, room, event):
        bot.must_be_admin(room, event)
        await bot.send_text(room, f'Quitting, as requested')
        print(f'{event.sender} commanded bot to quit, so quitting..')
        bot.bot_task.cancel()

    def help(self):
        return 'Bot management commands'
