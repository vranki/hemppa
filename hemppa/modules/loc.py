from geopy.geocoders import Nominatim
from nio import RoomMessageUnknown

from .common.module import BotModule


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.bot = None
        self.enabled_rooms = []

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot
        bot.client.add_event_callback(self.unknown_cb, RoomMessageUnknown)

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.unknown_cb)

    '''
    Location events are like: https://spec.matrix.org/v1.2/client-server-api/#mlocation
    {
    "content": {
        "body": "geo:61.49342512194717,23.765914658307736",
        "geo_uri": "geo:61.49342512194717,23.765914658307736",
        "msgtype": "m.location",
        "org.matrix.msc1767.text": "geo:61.49342512194717,23.765914658307736",
        "org.matrix.msc3488.asset": {
        "type": "m.pin"
        },
        "org.matrix.msc3488.location": {
        "description": "geo:61.49342512194717,23.765914658307736",
        "uri": "geo:61.49342512194717,23.765914658307736"
        },
        "org.matrix.msc3488.ts": 1653837929839
    },
    "room_id": "!xsBGdLYGrfYhGfLtHG:hacklab.fi",
    "type": "m.room.message"
    }

    BUT sometimes there's ; separating altitude??
    {
  "content": {
    "body": "geo:61.4704211,23.4864855;36.900001525878906",
    "geo_uri": "geo:61.4704211,23.4864855;36.900001525878906",
    "msgtype": "m.location",
    "org.matrix.msc1767.text": "geo:61.4704211,23.4864855;36.900001525878906",
    "org.matrix.msc3488.asset": {
      "type": "m.self"
    },
    "org.matrix.msc3488.location": {
      "description": "geo:61.4704211,23.4864855;36.900001525878906",
      "uri": "geo:61.4704211,23.4864855;36.900001525878906"
    },
    "org.matrix.msc3488.ts": 1653931683087
  },
  "origin_server_ts": 1653931683998,
  "sender": "@cos:hacklab.fi",
  "type": "m.room.message",
  "unsigned": {
    "age": 70
  },
  "event_id": "$6xXutKF9EppPMMdc4aQLZjHyd8My0rIZuNZEcuSIPws",
  "room_id": "!CLofqdurVWZCMpFnqM:hacklab.fi"
}
    '''

    async def unknown_cb(self, room, event):
        if event.msgtype != 'm.location':
            return
        if room.room_id not in self.enabled_rooms:
            return
        location_text = event.content['body']

        # Fallback if body is empty
        if (len(location_text) == 0) or ('geo:' in location_text):
            location_text = 'location'

        sender_response = await self.bot.client.get_displayname(event.sender)
        sender = sender_response.displayname

        geo_uri = event.content['geo_uri']
        try:
            geo_uri = geo_uri[4:] # Strip geo:

            if ';' in geo_uri: # Strip altitude, if present
                geo_uri = geo_uri.split(';')[0]
            latlon = geo_uri.split(',')

            # Sanity checks to avoid url manipulation
            float(latlon[0])
            float(latlon[1])
        except Exception:
            self.bot.send_text(room, "Error: Invalid location " + geo_uri)
            return

        osm_link = f"https://www.openstreetmap.org/?mlat={latlon[0]}&mlon={latlon[1]}"

        plain = f'{sender} sent {location_text} {osm_link} 🚩'
        html = f'{sender} sent <a href="{osm_link}">{location_text}</a> 🚩'

        await self.bot.send_html(room, html, plain)

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) == 0:
            await bot.send_text(room, 'Usage: !loc <location name>')
            return
        elif len(args) == 1:
            if args[0] == 'enable':
                bot.must_be_admin(room, event)
                self.enabled_rooms.append(room.room_id)
                self.enabled_rooms = list(dict.fromkeys(self.enabled_rooms)) # Deduplicate
                await bot.send_text(room, "Ok, sending locations events here as text versions")
                bot.save_settings()
                return
            if args[0] == 'disable':
                bot.must_be_admin(room, event)
                self.enabled_rooms.remove(room.room_id)
                await bot.send_text(room, "Ok, disabled here")
                bot.save_settings()
                return

        query = event.body[4:]
        geolocator = Nominatim(user_agent=bot.appid)
        self.logger.info('loc: looking up %s ..', query)
        location = geolocator.geocode(query)
        self.logger.info('loc rx %s', location)
        if location:
            await bot.send_location(room, location.address, location.latitude, location.longitude, "m.pin")
        else:
            await bot.send_text(room, "Can't find " + query + " on map!")

    def help(self):
        return 'Search for locations and display Matrix location events as OSM links'

    def get_settings(self):
        data = super().get_settings()
        data["enabled_rooms"] = self.enabled_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("enabled_rooms"):
            self.enabled_rooms = data["enabled_rooms"]
