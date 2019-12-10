from geopy.geocoders import Nominatim
from nio import (RoomMessageUnknown)

class MatrixModule:
    bot = None
    def matrix_start(self, bot):
        self.bot = bot
        bot.client.add_event_callback(self.unknown_cb, RoomMessageUnknown)

    async def unknown_cb(self, room, event):
        if event.msgtype != 'm.location':
            return

        location_text = event.content['body']

        # Fallback if body is empty
        if len(location_text) == 0:
            location_text = 'location'

        sender_response = await self.bot.client.get_displayname(event.sender)
        sender = sender_response.displayname

        geo_uri = event.content['geo_uri']
        latlon = geo_uri.split(':')[1].split(',')

        # Sanity checks to avoid url manipulation
        float(latlon[0])
        float(latlon[1])

        osm_link = 'https://www.openstreetmap.org/?mlat=' + latlon[0] + "&mlon=" + latlon[1]
        
        plain = sender + ' - ' + osm_link
        html = f'{sender} - <a href={osm_link}>{location_text}</a>'

        await self.bot.send_html(room, html, plain)

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        if len(args) == 0:
            await bot.send_text(room, 'Usage: !loc <location name>')
        if len(args) == 1:
            query = event.body[4:]
            geolocator = Nominatim(user_agent=bot.appid)
            location = geolocator.geocode(query)
            if location:
                locationmsg = {
                    "body": "Tampere, Finland",
                    "geo_uri": "geo:61.5,23.766667",
                    "msgtype": "m.location",
                }
                locationmsg['body'] = location.address
                locationmsg['geo_uri'] = 'geo:' + str(location.latitude) + ',' + str(location.longitude)
                await bot.client.room_send(bot.get_room_id(room), 'm.room.message', locationmsg)
            else:
                await bot.send_text(room, "Can't find " + query + " on map!")

    def help(self):
        return('Search for locations and display Matrix location events as OSM links')
