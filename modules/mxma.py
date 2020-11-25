from modules.common.module import BotModule
import requests, json
import traceback

from modules.common.pollingservice import PollingService

class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.service_name = 'MXMA'
        self.poll_interval_min = 5
        self.poll_interval_random = 2
        self.owner_only = True
        self.send_all = True
        self.enabled = False

    async def poll_implementation(self, bot, account, roomid, send_messages):
        try:
            response = requests.get(url=account, timeout=5)
            if response.status_code == 200:
                if 'messages' in response.json():
                    messages = response.json()['messages']
                    for message in messages:
                        success = await bot.send_msg(message['to'], message['title'], message['message'])
        except Exception:
            self.logger.error('Polling MXMA failed:')
            traceback.print_exc(file=sys.stderr)

    def help(self):
        return 'Matrix messaging API'
