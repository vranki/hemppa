from modules.common.module import BotModule
import requests


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.apiurl = ""
        self.deviceid = ""

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        if len(args) == 3:
            if args[0] == 'setdoor':
                bot.must_be_admin(room, event)

                self.apiurl = args[1]
                self.deviceid = args[2]
                self.logger.info(f'Adding api {self.apiurl} and device id {self.deviceid}')
                await bot.send_text(room, f'Adding api {self.apiurl} and device id {self.deviceid}')
                bot.save_settings()
                return
            
        myobj = { "deviceid": self.deviceid, "payload": event.sender}
        headers = {'Content-Type': 'application/json'}

        self.logger.info(f'User {event.sender} wants to open door')
        x = requests.post(self.apiurl, json = myobj, headers=headers)
        if x.status_code != 200:
            self.logger.info(f'User has no access')
            await bot.send_text(room, 'Sinulla ei ole tilankäyttöoikeutta')
            return

        self.logger.info(f'Opening door!')
        await bot.send_text(room, 'Avaan oven..')

    def get_settings(self):
        data = super().get_settings()
        data["apiurl"] = self.apiurl
        data["deviceid"] = self.deviceid
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("apiurl"):
            self.apiurl = data["apiurl"]
        if data.get("deviceid"):
            self.deviceid = data["deviceid"]

    def help(self):
        return 'Avaa hacklabin oven jos käyttäjällä tilankäyttöoikeus'
