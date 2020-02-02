import re
import urllib.request

from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 2 and len(args[1]) == 4:
            icao = args[1].upper()
            notam = self.get_notam(icao)
            await bot.send_text(room, notam)
        else:
            await bot.send_text(room, 'Usage: !notam <icao code>')

    def help(self):
        return ('NOTAM data access (usage: !notam <icao code>) - Currently Finnish airports only')

    # TODO: This handles only finnish airports. Implement support for other countries.
    def get_notam(self, icao):
        if not icao.startswith('EF'):
            return ('Only Finnish airports supported currently, sorry.')

        icao_first_letter = icao[2]
        if icao_first_letter < 'M':
            notam_url = "https://www.ais.fi/ais/bulletins/envfra.htm"
        else:
            notam_url = "https://www.ais.fi/ais/bulletins/envfrm.htm"

        response = urllib.request.urlopen(notam_url)
        lines = response.readlines()
        lines = b''.join(lines)
        lines = lines.decode("ISO-8859-1")
        # Strip EN-ROUTE from end
        lines = lines[0:lines.find('<a name="EN-ROUTE">')]

        startpos = lines.find('<a name="' + icao + '">')
        if startpos > -1:
            endpos = lines.find('<h3>', startpos)
            if endpos == -1:
                endpos = len(lines)
            notam = lines[startpos:endpos]
            notam = re.sub('<[^<]+?>', ' ', notam)
            if len(notam) > 4:
                return notam
        return f'Cannot parse notam for {icao} at {notam_url}'
