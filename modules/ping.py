from timeit import default_timer as timer
from urllib.request import urlopen

from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        url = args[0]

        # check url
        if not (url.startswith('http://') or url.startswith('https://')):
            self.logger.debug("adding trailing https")
            url = "https://" + url

        self.logger.info("ping: %s", url)

        start = timer()
        try:
            data = urlopen(url)
            length = format(len(data.read()) / 1024, '.3g')  # kB
            retcode = data.getcode()

        except Exception as e:
            await bot.send_text(room, "Ping failed: " + str(e))
            self.logger.error(str(e))
            return False

        end = timer()

        await bot.send_text(room, url + ": OK (" + str(retcode) + ") / " + "Size: " + str(length) +
                            " kB / Time: " + str(format(end - start, '.3g')) + " sec")

    def help(self):
        return 'check if IP or URL is accessible'
