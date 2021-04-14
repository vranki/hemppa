import sys
import traceback
import urllib.request
import json
import time
import datetime

from datetime import datetime, timedelta
from random import randrange

from modules.common.module import BotModule

class FlightBook:
    def __init__(self):
        self.base_url = 'https://flightbook.glidernet.org/api'
        self.AC_TYPES = [ '?', 'Glider', 'Towplane', \
            'Helicopter', 'Parachute', 'Drop plane', 'Hang glider', \
            'Paraglider', 'Powered', 'Jet', 'UFO', 'Balloon', \
            'Airship', 'UAV', '?', 'Static object' ]
        self.logged_flights = dict() # station -> [index of flight]

    def get_flights(self, icao):
        response = urllib.request.urlopen(self.base_url + "/logbook/" + icao)
        data = json.loads(response.read().decode("utf-8"))
        # print(json.dumps(data, sort_keys=True, indent=4))
        return data

    def format_time(self, time):
        if not time:
            return '··:··'
        time = time.replace('h', ':')
        return time

    def flight2string(self, flight, data):
        devices = data['devices']
        device = devices[flight['device']]
        start = self.format_time(flight["start"])
        end = self.format_time(flight["stop"])
        duration = '     '
        if flight["duration"]:
            duration = time.strftime('%H:%M', time.gmtime(flight["duration"]))
        maxalt = ''
        if flight["max_alt"]:
            maxalt = str(flight["max_alt"]) + 'm'
        
        identity = f'{device.get("registration") or ""} {device.get("aircraft") or ""} {device.get("competition") or ""} {maxalt}'
        identity = ' '.join(identity.split())
        return f'{start} - {end} {duration} {identity}'

    def print_flights(self, data, showtow=False):
        print(f'✈ Flights at {data["airfield"]["name"]} ({data["airfield"]["code"]}) {data["date"]}:')
        flights = data['flights']
        for flight in flights:
            if not showtow and flight["towing"]:
                continue
            print(self.flight2string(flight, data))

    def test():
        fb = FlightBook()
        data = fb.get_flights('LFMX')
        fb.print_flights(data)

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.service_name = 'FLOG'
        self.station_rooms = dict()  # Roomid -> ogn station
        self.live_rooms = []     # Roomid's with live enabled
        self.logged_flights = dict() # Station -> number of flights
        self.first_poll = True
        self.enabled = False
        self.fb = FlightBook()

    async def matrix_poll(self, bot, pollcount):
        if pollcount % (6 * 5) == 0:  # Poll every 5 min
            await self.poll_implementation(bot)

    async def poll_implementation(self, bot):
        for roomid in self.live_rooms:
            station = self.station_rooms[roomid]
            data = self.fb.get_flights(station)

            flights = data['flights']

            if len(flights) == 0 or (not station in self.logged_flights):
                self.logged_flights[station] = []
                #print('Reset flight count for station ' + station)
#            else:
#                print(f'Got {len(flights)} flights at {station}')

            flightindex = 0
            for flight in flights:
                if flight["towing"]:
                    continue
                if flight["stop"]:
                    if not flightindex in self.logged_flights[station]:
                        if not self.first_poll:
                            await bot.send_text(bot.get_room_by_id(roomid), self.fb.flight2string(flight, data))
                        self.logged_flights[station].append(flightindex)
                        # print(f'Logged flights at {station} now {self.logged_flights[station]}')
                flightindex = flightindex + 1
        self.first_poll = False

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 1:
            if room.room_id in self.station_rooms:
                station = self.station_rooms[room.room_id]
                await self.show_flog(bot, room, station)
            else:
                await bot.send_text(room, 'No OGN station set for this room - set it first.')

        elif len(args) == 2:
            if args[1] == 'rmstation':
                bot.must_be_admin(room, event)
                del self.station_rooms[room.room_id]
                self.live_rooms.remove(room.room_id)
                await bot.send_text(room, f'Cleared OGN station for this room')

            elif args[1] == 'status':
                print(self.logged_flights)
                bot.must_be_admin(room, event)
                await bot.send_text(room, f'OGN station for this room: {self.station_rooms.get(room.room_id)}, live updates enabled: {room.room_id in self.live_rooms}')

            elif args[1] == 'poll':
                bot.must_be_admin(room, event)
                await self.poll_implementation(bot)

            elif args[1] == 'live':
                bot.must_be_admin(room, event)
                self.live_rooms.append(room.room_id)
                bot.save_settings()
                await bot.send_text(room, f'Sending live updates for station {self.station_rooms.get(room.room_id)} to this room')

            elif args[1] == 'rmlive':
                bot.must_be_admin(room, event)
                self.live_rooms.remove(room.room_id)
                bot.save_settings()
                await bot.send_text(room, f'Not sending live updates for station {self.station_rooms.get(room.room_id)} to this room anymore')

            else:
                # Assume parameter is a station name
                station = args[1]
                await self.show_flog(bot, room, station)

        elif len(args) == 3:
            if args[1] == 'station':
                bot.must_be_admin(room, event)

                station = args[2]
                self.station_rooms[room.room_id] = station
                self.logger.info(f'Station now for this room {self.station_rooms.get(room.room_id)}')

                bot.save_settings()
                await bot.send_text(room, f'Set OGN station {station} to this room')

    def text_flog(self, data, showtow):
        out = ""
        if len(data["flights"]) == 0:
            out = f'No known flights today at {data["airfield"]["name"]}'
        else:
            out = f'Flights at {data["airfield"]["name"]} ({data["airfield"]["code"]}) {data["date"]}:' + "\n"
            flights = data['flights']
            for flight in flights:
                if not showtow and flight["towing"]:
                    continue
                out = out + self.fb.flight2string(flight, data) + "\n"
        return out

    def html_flog(self, data, showtow):
        out = ""
        if len(data["flights"]) == 0:
            out = f'No known flights today at {data["airfield"]["name"]}'
        else:
            out = f'<b>✈ Flights at {data["airfield"]["name"]} ({data["airfield"]["code"]}) {data["date"]}:' + "</b>\n"
            flights = data['flights']
            out = out + "<ul>"
            for flight in flights:
                if not showtow and flight["towing"]:
                    continue
                out = out + "<li>" + self.fb.flight2string(flight, data) + "</li>\n"
            out = out + "</ul>"
        return out

    async def show_flog(self, bot, room, station):
        data = self.fb.get_flights(station)
        await bot.send_html(room, self.html_flog(data, False), self.text_flog(data, False))

    def get_settings(self):
        data = super().get_settings()
        data['station_rooms'] = self.station_rooms
        data['live_rooms'] = self.live_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('station_rooms'):
            self.station_rooms = data['station_rooms']
        if data.get('live_rooms'):
            self.live_rooms = data['live_rooms']

    def help(self):
        return ('Open Glider Network Field Log')
