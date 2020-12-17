import urllib.request
import wolframalpha

from modules.common.module import BotModule


class MatrixModule(BotModule):
    app_id = ''

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 3:
            if args[1] == "appid":
                bot.must_be_owner(event)
                self.app_id = args[2]
                bot.save_settings()
                await bot.send_text(room, 'App id set')
                print('Appid', self.app_id)
                return

        if len(args) > 1:
            if self.app_id == '':
                await bot.send_text(room, 'Please get and set a appid: https://products.wolframalpha.com/simple-api/documentation/')
                return

            query = event.body[len(args[0])+1:]
            client = wolframalpha.Client(self.app_id)
            answer = query + ': '
            try:
                res = client.query(query)
                result = "?SYNTAX ERROR"
                if res['@success']=='true':
                    pod0=res['pod'][0]['subpod']['plaintext']
                    pod1=res['pod'][1]
                    if (('definition' in pod1['@title'].lower()) or ('result' in  pod1['@title'].lower()) or (pod1.get('@primary','false') == 'true')):
                        result = pod1['subpod']['plaintext']
                answer += result + "\n"
            except Exception as exc:
                answer = "Wolfram Alpha has technical difficulty: " + str(exc)

            await bot.send_text(room, answer)
        else:
            await bot.send_text(room, 'Usage: !wa <query>')

    def get_settings(self):
        data = super().get_settings()
        data['app_id'] = self.app_id
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("app_id"):
            self.app_id = data["app_id"]

    def help(self):
        return ('Wolfram Alpha search')
