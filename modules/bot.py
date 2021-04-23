import collections
import json
from datetime import datetime

from modules.common.module import BotModule


class MatrixModule(BotModule):

    def __init__(self, name):
        super().__init__(name)
        self.starttime = None
        self.can_be_disabled = False

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.starttime = datetime.now()

    async def matrix_message(self, bot, room, event):
        args = event.body.split(None, 2)

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
            elif args[1] == 'modules':
                await self.show_modules(bot, room)
            elif args[1] == 'export':
                await self.export_settings(bot, event)

        elif len(args) == 3:
            if args[1] == 'enable':
                await self.enable_module(bot, room, event, args[2])
            elif args[1] == 'disable':
                await self.disable_module(bot, room, event, args[2])
            elif args[1] == 'export':
                await self.export_settings(bot, event, module_name=args[2])
            elif args[1] == 'import':
                await self.import_settings(bot, event)
        else:
            pass

        # TODO: Make this configurable. By default don't say anything.
        #    await bot.send_text(room, 'Unknown command, sorry.')

    async def leave(self, bot, room, event):
        bot.must_be_admin(room, event)
        self.logger.info(f'{event.sender} asked bot to leave room {room.room_id}')
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
        bot.must_be_owner(event)
        await bot.send_text(room, f'Reloading modules..')
        bot.stop()
        bot.reload_modules()
        bot.start()

    async def version(self, bot, room):
        await bot.send_text(room, f'Hemppa version {bot.version} - https://github.com/vranki/hemppa')

    async def quit(self, bot, room, event):
        bot.must_be_owner(event)
        await bot.send_text(room, f'Quitting, as requested')
        self.logger.info(f'{event.sender} commanded bot to quit, so quitting..')
        bot.bot_task.cancel()

    async def enable_module(self, bot, room, event, module_name):
        bot.must_be_owner(event)
        self.logger.info(f"Asked to enable {module_name}")
        if bot.modules.get(module_name):
            module = bot.modules.get(module_name)
            module.enable()
            module.matrix_start(bot)
            bot.save_settings()
            await bot.send_text(room, f"module {module_name} enabled")
        else:
            await bot.send_text(room, f"module with name {module_name} not found. execute !bot modules for a list of available modules")

    async def disable_module(self, bot, room, event, module_name):
        bot.must_be_owner(event)
        self.logger.info(f"asked to disable {module_name}")
        if bot.modules.get(module_name):
            module = bot.modules.get(module_name)
            if module.can_be_disabled:
                module.disable()
                module.matrix_stop(bot)
                bot.save_settings()
                await bot.send_text(room, f"module {module_name} disabled")
            else:
                await bot.send_text(room, f"module {module_name} cannot be disabled")
        else:
            await bot.send_text(room, f"module with name {module_name} not found. execute !bot modules for a list of available modules")

    async def show_modules(self, bot, room):
        modules_message = "Modules:\n"
        for modulename, module in collections.OrderedDict(sorted(bot.modules.items())).items():
            state = 'Enabled' if module.enabled else 'Disabled'
            modules_message += f"{state}: {modulename} - {module.help()}\n"
        await bot.send_text(room, modules_message)

    async def export_settings(self, bot, event, module_name=None):
        bot.must_be_owner(event)
        data = bot.get_account_data()['module_settings']
        if module_name:
            data = data[module_name]
            self.logger.info(f"{event.sender} is exporting settings for module {module_name}")
        else:
            self.logger.info(f"{event.sender} is exporting all settings")
        await bot.send_msg(event.sender, f'Private message from {bot.matrix_user}', json.dumps(data))

    async def import_settings(self, bot, event):
        bot.must_be_owner(event)

        self.logger.info(f"{event.sender} is importing settings")
        try:
            account_data = bot.get_account_data()
            child = account_data['module_settings']
        except KeyError: # no data yet
            account_data['module_settings'] = dict()
            child = account_data['module_settings']

        key = None
        data = event.body.split(None, 2)[2]
        while not data.startswith('{'):
            key, data = data.split(None, 1)
            if child.get(key):
                child = child[key]
                key = None
            else:
                break
        data = json.loads(data)

        if not key:
            child.update(data)
        else:
            child[key] = data
        bot.load_settings(account_data)
        bot.save_settings()
        await bot.send_msg(event.sender, f'Private message from {bot.matrix_user}', 'Updated bot settings')

    def help(self):
        return 'Bot management commands. (quit, version, reload, status, stats, leave, modules, enable, disable)'
