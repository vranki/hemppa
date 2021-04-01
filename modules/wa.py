import urllib.request
import wolframalpha

from modules.common.module import BotModule


class MatrixModule(BotModule):
    app_id = ''

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, ['wafull'])

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
            res = client.query(query)
            result = "?SYNTAX ERROR"
            if res['@success']:
                self.logger.debug(f"room: {room.name} sender: {event.sender} sent a valid query to wa")
            else:
                self.logger.info(f"wa error: {res['@error']}")
            primary, items, fallback = self.parse_api_response(res)
            if len(items) and 'full' in args[0]:
                answer = '\n'.join(items)
            elif primary:
                answer = query + ': ' + primary
            elif fallback:
                answer = query + ': ' + fallback
            else:
                answer = 'Could not find response for ' + query

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

    def parse_api_response(self, res, key='plaintext'):
        fallback = None
        primary = None
        items = list()
        # workaround for bug in upstream wa package
        if hasattr(res['pod'], 'get'):
            res['pod'] = [res['pod']]
        for pod in res['pod']:
            title = pod['@title'].lower()
            if 'input' in title:
                continue
            for sub in pod.subpods:
                print(sub)
                item = sub.get(key)
                if not item:
                    continue
                items.append(item)
                fallback = fallback or item
                if ('definition' in title) or ('result' in title) or pod.get('@primary'):
                    primary = primary or item
        return (primary, items, fallback)

    def help(self):
        return ('Wolfram Alpha search')
