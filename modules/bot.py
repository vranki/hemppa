import urllib.request
from datetime import datetime, timedelta

class MatrixModule:
    def matrix_start(self, bot):
        self.starttime = datetime.now()

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2:
            if args[1]=='quit':
                bot.must_be_admin(room, event)
                await bot.send_text(room, f'Quitting, as requested')
                print(f'{event.sender} commanded bot to quit, so quitting..')
                bot.bot_task.cancel()
            elif args[1]=='version':
                await bot.send_text(room, f'Hemppa version {bot.version} - https://github.com/vranki/hemppa')
            elif args[1]=='reload':
                bot.must_be_admin(room, event)
                await bot.send_text(room, f'Reloading modules..')
                bot.stop()
                bot.reload_modules()
                bot.start()
            elif args[1]=='status':
                uptime = datetime.now() - self.starttime
                await bot.send_text(room, f'Uptime {uptime} - system time is {datetime.now()} - loaded {len(bot.modules)} modules.')
            elif args[1]=='stats':
                roomcount = len(bot.client.rooms)
                usercount = 0
                homeservers = dict()

                for croomid in bot.client.rooms:
                    room = bot.client.rooms[croomid]
                    usercount = usercount + len(room.users)
                    for user in room.users:
                        hs = user.split(':')[1]
                        if homeservers.get(hs):
                            homeservers[hs] = homeservers[hs] + 1
                        else:
                            homeservers[hs] = 1

                homeservers = sorted(homeservers.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

                if len(homeservers) > 10:
                    homeservers = homeservers[0:10]

                await bot.send_text(room, f'I\'m seeing {usercount} users in {roomcount} rooms. Top ten homeservers: {homeservers}')
        else:
            await bot.send_text(room, 'Unknown command, sorry.')

    def help(self):
        return('Bot management commands')
