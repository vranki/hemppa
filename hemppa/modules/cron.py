import shlex
import os
from datetime import datetime

from .common.module import BotModule


class MatrixModule(BotModule):
    daily_commands = dict()  # room_id -> command json
    last_hour = datetime.now().hour

    async def matrix_message(self, bot, room, event):
        bot.must_be_admin(room, event)

        args = shlex.split(event.body)
        args.pop(0)
        if len(args) == 3:
            if args[0] == 'daily':
                dailytime = int(args[1])
                dailycmd = args[2]
                if not self.daily_commands.get(room.room_id):
                    self.daily_commands[room.room_id] = []
                self.daily_commands[room.room_id].append(
                    {'time': dailytime, 'command': dailycmd})
                bot.save_settings()
                await bot.send_text(room, 'Daily command added.')
        elif len(args) == 1:
            if args[0] == 'list':
                await bot.send_text(room, 'Daily commands on this room: ' + str(self.daily_commands.get(room.room_id)))
            elif args[0] == 'clear':
                self.daily_commands.pop(room.room_id, None)
                bot.save_settings()
                await bot.send_text(room, 'Cleared commands on this room.')
            elif args[0] == 'time':
                await bot.send_text(room, '{datetime} {timezone}'.format(datetime=datetime.now(), timezone=os.environ.get('TZ')))

    def help(self):
        return ('Runs scheduled commands')

    def get_settings(self):
        data = super().get_settings()
        data['daily_commands'] = self.daily_commands
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('daily_commands'):
            self.daily_commands = data['daily_commands']

    async def matrix_poll(self, bot, pollcount):
        delete_rooms = []
        if self.last_hour != datetime.now().hour:
            self.last_hour = datetime.now().hour

            for room_id in self.daily_commands:
                if room_id in bot.client.rooms:
                    commands = self.daily_commands[room_id]
                    for command in commands:
                        if int(command['time']) == self.last_hour:
                            await bot.send_text(bot.get_room_by_id(room_id), command['command'], 'm.text')
                else:
                    delete_rooms.append(room_id)

        for roomid in delete_rooms:
            self.daily_commands.pop(roomid, None)
