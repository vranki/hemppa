import sys
import traceback
import urllib.request
import json
import time
import datetime

from datetime import datetime, timedelta
from random import randrange

from modules.common.module import BotModule

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.service_name = 'FLOG'
        self.station_rooms = dict()  # Roomid -> ogn station
        self.live_rooms = []     # Roomid's with live enabled
        self.room_timezones = dict()  # Roomid -> timezone
        self.api_key = ''
        self.logged_flights = []
        self.logged_flights_date = ""
        self.first_poll = True

    async def matrix_poll(self, bot, pollcount):
        if len(self.api_key) > 0:
            if pollcount % (6 * 5) == 0:  # Poll every 5 min
                await self.poll_implementation(bot)

    async def poll_implementation(self, bot):
        for roomid in self.live_rooms:
            station = self.station_rooms[roomid]
            data = self.get_flights(station, self.room_timezones.get(roomid, 0))

            # Date changed - reset flight count
            if data["begin_date"] != self.logged_flights_date:
                self.logged_flights = []
                self.logged_flights_date = data["begin_date"]

            flights = []

            for sortie in data["sorties"]:
                # Don't show towplanes
                if sortie["type"] != 2:
                    # Count only landed gliders
                    if sortie["ldg"]["time"] != "":
                        flights.append(
                            { 
                                "takeoff": sortie["tkof"]["time"], 
                                "landing": sortie["ldg"]["time"],
                                "duration": sortie["dt"],
                                "glider": self.glider2string(sortie),
                                "altitude": str(sortie["dalt"]),
                                "seq": sortie["seq"]
                            })
            for flight in flights:
                if flight["seq"] not in self.logged_flights:
                    if not self.first_poll:
                        await bot.send_text(bot.get_room_by_id(roomid), flight["takeoff"] + "-" + flight["landing"] + " (" + flight["duration"] + ") - " + flight["altitude"] + "m " + flight["glider"])
                    self.logged_flights.append(flight["seq"])
        self.first_poll = False

    def get_flights(self, station, timezone):
        timenow = time.localtime(time.time())
        today = str(timenow[0]) + "-" + str(timenow[1]) + "-" + str(timenow[2])
        # Example 'https://ktrax.kisstech.ch/backend/logbook?db=sortie&query_type=ap&tz=3&id=ESGE&dbeg=2020-05-03&dend=2020-05-03'
        log_url = f'https://ktrax.kisstech.ch/backend/logbook?db=sortie&query_type=ap&tz={timezone}&id={station}&dbeg={today}&dend={today}&apikey={self.api_key}'
        response = urllib.request.urlopen(log_url)
        data = json.loads(response.read().decode("utf-8"))
        # print(json.dumps(data, sort_keys=True, indent=4))
        return data

    def glider2string(self, sortie):
        actype = sortie["actype"]
        cs = sortie["cs"]
        cn = sortie["cn"]
        if cs == "-":
            cs = ""
        if cn == "-":
            cn = ""

        if actype == "" and cs == "" and cn == "":
            return "????"
        return (actype + " " + cs + " " + cn).strip()


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
                bot.must_be_admin(room, event)
                await bot.send_text(room, f'OGN station for this room: {self.station_rooms.get(room.room_id)}, live updates enabled: {room.room_id in self.live_rooms}, timezone: {self.room_timezones.get(room.room_id, 0)} api key is set: {len(self.api_key) > 0}')

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

            elif args[1] == 'apikey':
                bot.must_be_owner(event)

                self.api_key = args[2]
                bot.save_settings()
                await bot.send_text(room, 'Api key set')

            elif args[1] == 'timezone':
                bot.must_be_admin(room, event)
                tz = int(args[2])
                self.room_timezones[room.room_id] = tz
                bot.save_settings()
                await bot.send_text(room, f'Timezone set to {tz}')

    async def show_flog(self, bot, room, station):
        data = self.get_flights(station, self.room_timezones.get(room.room_id, 0))
        out = ""
        if len(data["sorties"]) == 0:
            out = "No known flights today at " + station
        else:
            out = "Flights at " + station.upper() + " today:\n"
            for sortie in data["sorties"]:
                # Don't show towplanes
                if sortie["type"] != 2:
                    if sortie["ldg"]["time"] == "":
                        sortie["ldg"]["time"] = u"  \u2708  "
                    else:
                        sortie["ldg"]["time"] = "-" + sortie["ldg"]["time"]
                        if sortie["ldg"]["loc"] != sortie["tkof"]["loc"]:
                            sortie["tkof"]["time"] = sortie["tkof"]["time"] + "(" + sortie["tkof"]["loc"] + ")"
                            sortie["ldg"]["time"] = sortie["ldg"]["time"] + "(" + sortie["ldg"]["loc"] + ") "

                    out = out + sortie["tkof"]["time"] + sortie["ldg"]["time"] + " " + sortie["dt"] + " " + str(sortie["dalt"]) + "m " + self.glider2string(sortie) + "\n"
        await bot.send_text(room, out)

    def get_settings(self):
        data = super().get_settings()
        data['apikey'] = self.api_key
        data['station_rooms'] = self.station_rooms
        data['live_rooms'] = self.live_rooms
        data['room_timezones'] = self.room_timezones
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('station_rooms'):
            self.station_rooms = data['station_rooms']
        if data.get('live_rooms'):
            self.live_rooms = data['live_rooms']
        if data.get('room_timezones'):
            self.room_timezones = data['room_timezones']
        if data.get('apikey'):
            self.api_key = data['apikey']
        if self.api_key and len(self.api_key) == 0:
            self.api_key = None

    def help(self):
        return ('Open Glider Network Field Log')
