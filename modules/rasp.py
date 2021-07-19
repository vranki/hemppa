from modules.common.module import BotModule
import urllib.request

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        day = 0
        hour = 12
        if len(args) >= 1:
            day = int(args[0]) - 1
        if len(args) == 2:
            hour = int(args[1])

        imgurl = 'http://ennuste.ilmailuliitto.fi/' + str(day) + '/wstar_bsratio.curr.' + str(hour) + '00lst.d2.png'
        await bot.upload_and_send_image(room, imgurl, f"RASP Day {day+1} at {hour}:00", no_cache=True)

    def help(self):
        return 'RASP Gliding Weather forecast, Finland only'
