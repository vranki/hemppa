import requests

from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2:
            icao = args[1].upper()
            taf_url = "https://aviationweather.gov/api/data/taf?ids=" + icao
            response = requests.get(taf_url)
            if len(response.text) > 0:
                await bot.send_text(room, response.text)
            else:
                await bot.send_text(room, 'Cannot find taf for ' + icao)
        else:
            await bot.send_text(room, 'Usage: !taf <icao code>')

    def help(self):
        return ('Taf data access (usage: !taf <icao code>)')
