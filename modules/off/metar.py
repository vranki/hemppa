import urllib.request

from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2:
            icao = args[1]
            metar_url = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/" + \
                        icao.upper() + ".TXT"
            response = urllib.request.urlopen(metar_url)
            lines = response.readlines()
            await bot.send_text(room, lines[1].decode("utf-8").strip())
        else:
            await bot.send_text(room, 'Usage: !metar <icao code>')

    def help(self):
        return ('Metar data access (usage: !metar <icao code>)')
