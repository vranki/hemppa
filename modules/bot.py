import collections
import json
import requests
from datetime import timedelta
import time

from modules.common.module import BotModule, ModuleCannotBeDisabled

class MatrixModule(BotModule):

    def __init__(self, name):
        super().__init__(name)
        self.starttime = None
        self.can_be_disabled = False

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.starttime = time.time()

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
            elif args[1] == 'ping':
                await self.get_ping(bot, room, event)

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

    async def get_ping(self, bot, room, event):
        self.logger.info(f'{event.sender} pinged the bot in {room.room_id}')

        # initial pong
        serv_before  = event.server_timestamp
        local_before = time.time()
        pong = await bot.client.room_send(room.room_id, 'm.room.message',
            {'body': f'Pong!', 'msgtype': 'm.notice'})
        local_delta = int((time.time() - local_before) * 1000)

        # ask the server what the timestamp was on our pong
        serv_delta = None
        event_url = f'{bot.client.homeserver}/_matrix/client/r0/rooms/{room.room_id}/event/{pong.event_id}?access_token={bot.client.access_token}'
        try:
            serv_delta = requests.get(event_url).json()['origin_server_ts'] - serv_before
            delta = f'server response in {local_delta}ms, event created in {serv_delta}ms'
        except Exception as e:
            self.logger.error(f"Failed getting server timestamp: {e}")
            delta = f'server response in {local_delta}ms'

        # update event
        content = {
            'm.new_content': {
                'msgtype': 'm.notice',
                'body': f'Pong! ({delta})'
            },
            'm.relates_to': {
                'rel_type': 'm.replace',
                'event_id': pong.event_id
            },
            'msgtype': 'm.notice',
            'body': delta
        }
        await bot.client.room_send(room.room_id, 'm.room.message', content)

    async def leave(self, bot, room, event):
        bot.must_be_admin(room, event)
        self.logger.info(f'{event.sender} asked bot to leave room {room.room_id}')
        await bot.send_text(room, f'By your command.')
        await bot.client.room_leave(room.room_id)

    async def stats(self, bot, room):
        roomcount = len(bot.client.rooms)
        homeservers = dict()
        for croomid in bot.client.rooms:
            try:
                users = bot.client.rooms[croomid].users
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Couldn't get user list in room with id {croomid}, skipping: {repr(e)}")
                continue
            for user in users:
                user, hs = user.split(':', 1)
                if homeservers.get(hs):
                    homeservers[hs].add(user)
                else:
                    homeservers[hs] = {user}
        homeservers = {k: len(v) for k, v in homeservers.items()}
        usercount = sum(homeservers.values())
        hscount = len(homeservers)
        homeservers = sorted(homeservers.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
        homeservers = ', '.join(['{} ({} users, {:.1f}%)'.format(hs[0], hs[1], 100.0 * hs[1] / usercount)
            for hs in homeservers[:10]])
        await bot.send_text(room, f'I\'m seeing {usercount} users in {roomcount} rooms.'
                f' Top ten homeservers (out of {hscount}): {homeservers}')

    async def status(self, bot, room):
        systime = time.time()
        uptime  = str(timedelta(seconds=(systime - self.starttime))).split('.', 1)[0]
        systime = time.ctime(systime)
        enabled = sum(1 for module in bot.modules.values() if module.enabled)

        return await bot.send_text(room, f'Uptime: {uptime} - System time: {systime} '
                f'- {enabled} modules enabled out of {len(bot.modules)} loaded.')

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
            return await bot.send_text(room, f"Module {module_name} enabled")
        return await bot.send_text(room, f"Module with name {module_name} not found. Execute !bot modules for a list of available modules")

    async def disable_module(self, bot, room, event, module_name):
        bot.must_be_owner(event)
        self.logger.info(f"asked to disable {module_name}")
        if bot.modules.get(module_name):
            module = bot.modules.get(module_name)
            try:
                module.disable()
            except ModuleCannotBeDisabled:
                return await bot.send_text(room, f"Module {module_name} cannot be disabled.")
            except Exception as e:
                return await bot.send_text(room, f"Module {module_name} was not disabled: {repr(e)}")
            module.matrix_stop(bot)
            bot.save_settings()
            return await bot.send_text(room, f"Module {module_name} disabled")
        return await bot.send_text(room, f"Module with name {module_name} not found. Execute !bot modules for a list of available modules")

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

    def disable(self):
        raise ModuleCannotBeDisabled

    def help(self):
        return 'Bot management commands. (quit, version, reload, status, stats, leave, modules, enable, disable, import, export, ping)'

    def long_help(self, bot=None, event=None, **kwargs):
        text = self.help() + (
                '\n- "!bot version": get bot version'
                '\n- "!bot ping": get the ping time to the server'
                '\n- "!bot status": get bot uptime and status'
                '\n- "!bot stats": get current users, rooms, and homeservers')
        if bot and event and bot.is_owner(event):
            text += ('\n- "!bot quit": kill the bot :('
                     '\n- "!bot reload": reload the bot modules'
                     '\n- "!bot enable [module]": enable a module'
                     '\n- "!bot disable [module]": disable a module'
                     '\n- "!bot import ([module]) [json]": import settings into the bot'
                     '\n- "!bot export ([module])": export settings from the bot'
                     )
        return text

