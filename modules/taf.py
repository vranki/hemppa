import urllib.request

from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2:
            icao = args[1]
            taf_url = "https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=csv&hoursBeforeNow=3&timeType=issue&mostRecent=true&stationString=" + icao.upper()
            response = urllib.request.urlopen(taf_url)
            lines = response.readlines()
            if len(lines) > 6:
                taf = lines[6].decode("utf-8").split(',')[0]
                await bot.send_text(room, taf.strip())
            else:
                await bot.send_text(room, 'Cannot find taf for ' + icao)
        else:
            await bot.send_text(room, 'Usage: !taf <icao code>')

    def help(self):
        return ('Taf data access (usage: !taf <icao code>)')
