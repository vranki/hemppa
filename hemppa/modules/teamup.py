import time
from datetime import datetime

from pyteamup import Calendar

#
# TeamUp calendar notifications
#
from modules.common.module import BotModule


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.api_key = None
        self.calendar_rooms = dict()  # Roomid -> [calid, calid..]
        self.calendars = dict()  # calid -> Calendar
        self.enabled = False

    async def matrix_poll(self, bot, pollcount):
        if self.api_key:
            if pollcount % (6 * 5) == 0:  # Poll every 5 min
                await self.poll_all_calendars(bot)

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 1:
            if self.calendar_rooms.get(room.room_id):
                for calendarid in self.calendar_rooms.get(room.room_id):
                    calendar = self.calendars[calendarid]
                    events = calendar.get_event_collection()
                    for event in events:
                        s = '<b>' + str(event.start_dt.day) + \
                            '.' + str(event.start_dt.month)
                        if not event.all_day:
                            s = s + ' ' + \
                                event.start_dt.strftime(
                                    "%H:%M") + ' (' + str(event.duration) + ' min)'
                        s = s + '</b> ' + event.title + \
                            " " + (event.notes or '')
                        await bot.send_html(room, s, s)
        elif len(args) == 2:
            if args[1] == 'list':
                await bot.send_text(room, f'Calendars in this room: {self.calendar_rooms.get(room.room_id) or []}')
            elif args[1] == 'poll':
                bot.must_be_owner(event)
                await self.poll_all_calendars(bot)
        elif len(args) == 3:
            if args[1] == 'add':
                bot.must_be_admin(room, event)

                calid = args[2]
                self.logger.info(f'Adding calendar {calid} to room id {room.room_id}')

                if self.calendar_rooms.get(room.room_id):
                    if calid not in self.calendar_rooms[room.room_id]:
                        self.calendar_rooms[room.room_id].append(calid)
                    else:
                        await bot.send_text(room, 'This teamup calendar already added in this room!')
                        return
                else:
                    self.calendar_rooms[room.room_id] = [calid]

                self.logger.info(f'Calendars now for this room {self.calendar_rooms.get(room.room_id)}')

                bot.save_settings()
                self.setup_calendars()
                await bot.send_text(room, 'Added new teamup calendar to this room')
            if args[1] == 'del':
                bot.must_be_admin(room, event)

                calid = args[2]
                self.logger.info(f'Removing calendar {calid} from room id {room.room_id}')

                if self.calendar_rooms.get(room.room_id):
                    self.calendar_rooms[room.room_id].remove(calid)

                self.logger.info(f'Calendars now for this room {self.calendar_rooms.get(room.room_id)}')

                bot.save_settings()
                self.setup_calendars()
                await bot.send_text(room, 'Removed teamup calendar from this room')
            if args[1] == 'apikey':
                bot.must_be_owner(event)

                self.api_key = args[2]
                bot.save_settings()
                self.setup_calendars()
                await bot.send_text(room, 'Api key set')

    def help(self):
        return ('Polls teamup calendar.')

    async def poll_all_calendars(self, bot):
        delete_rooms = []
        for roomid in self.calendar_rooms:
            if roomid in bot.client.rooms:
                calendars = self.calendar_rooms[roomid]
                for calendarid in calendars:
                    events, timestamp = self.poll_server(
                        self.calendars[calendarid])
                    self.calendars[calendarid].timestamp = timestamp
                    for event in events:
                        await bot.send_text(bot.get_room_by_id(roomid), 'Calendar: ' + self.eventToString(event))
            else:
                delete_rooms.append(roomid)

        for roomid in delete_rooms:
            self.calendar_rooms.pop(roomid, None)

    def poll_server(self, calendar):
        events, timestamp = calendar.get_changed_events(calendar.timestamp)
        return events, timestamp

    def to_datetime(self, dts):
        try:
            return datetime.strptime(dts, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            pos = len(dts) - 3
            dts = dts[:pos] + dts[pos + 1:]
            return datetime.strptime(dts, '%Y-%m-%dT%H:%M:%S%z')

    def eventToString(self, event):
        startdt = self.to_datetime(event['start_dt'])
        if len(event['title']) == 0:
            event['title'] = '(empty name)'

        if (event['delete_dt']):
            s = event['title'] + ' deleted.'
        else:
            s = event['title'] + " " + (event['notes'] or '') + \
                ' ' + str(startdt.day) + '.' + str(startdt.month)
            if not event['all_day']:
                s = s + ' ' + \
                    startdt.strftime("%H:%M") + \
                    ' (' + str(event['duration']) + ' min)'
        # todo: proper html stripper..
        s = s.replace('<p>', '')
        s = s.replace('</p>', '\n')
        return s

    def setup_calendars(self):
        self.calendars = dict()
        if self.api_key:
            for roomid in self.calendar_rooms:
                calendars = self.calendar_rooms[roomid]
                for calid in calendars:
                    self.calendars[calid] = Calendar(calid, self.api_key)
                    self.calendars[calid].timestamp = int(time.time())

    def get_settings(self):
        data = super().get_settings()
        data['apikey'] = self.api_key
        data['calendar_rooms'] = self.calendar_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('calendar_rooms'):
            self.calendar_rooms = data['calendar_rooms']
        if data.get('apikey'):
            self.api_key = data['apikey']
        if self.api_key and len(self.api_key) == 0:
            self.api_key = None
        self.setup_calendars()
