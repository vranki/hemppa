from modules.common.pollingservice import PollingService
from urllib.request import urlopen
import json
import time

class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.accountroomid_laststatus = {}
        self.template = '{spacename} is now {open_closed}'
        self.i18n = {'open': 'open 🔓', 'closed': 'closed 🔒'}

    async def poll_implementation(self, bot, account, roomid, send_messages):
        self.logger.debug(f'polling space api {account}.')
        spacename, is_open = MatrixModule.open_status(account)

        open_str = self.i18n['open'] if is_open else self.i18n['closed']
        text = self.template.format(spacename=spacename, open_closed=open_str)
        self.logger.debug(text)

        last_status = self.accountroomid_laststatus.get(account+roomid, False)
        if send_messages and last_status != is_open:
            await bot.send_text(bot.get_room_by_id(roomid), text)
            self.accountroomid_laststatus[account+roomid] = is_open
            bot.save_settings()

    @staticmethod
    def open_status(spaceurl):
        with urlopen(spaceurl, timeout=5) as response:
            js = json.load(response)

        return js['space'], js['state']['open']

    def get_settings(self):
        data = super().get_settings()
        data['laststatus'] = self.accountroomid_laststatus
        data['template'] = self.template
        data['i18n'] = self.i18n
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('laststatus'):
            self.accountroomid_laststatus = data['laststatus']
        if data.get('template'):
            self.template = data['template']
        if data.get('i18n'):
            self.i18n = data['i18n']

    def help(self):
        return "Notify about Space-API status changes (open or closed)."

    def long_help(self, bot, event, **kwargs):
        text = self.help() + \
            ' This is a polling service. Therefore there are additional ' + \
            'commands: list, debug, poll, clear, add URL, del URL\n' + \
            '!spaceapi add URL: to add a space-api endpoint\n' + \
            '!spaceapi list: to list the endpoint configured for this room.\n' + \
            f'I will look for changes roughly every {self.poll_interval_min} ' + \
            'minutes. Find out more about Space-API at https://spaceapi.io/.'
        if bot.is_owner(event):
            text += '\nA template and I18N can be configured via settings of ' + \
                'the module. Use "!bot export spacepi", then change the ' + \
                'settings and import again with "!bot import spacepi SETTINGS".'

        return text
