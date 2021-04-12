from typing import Text
import urllib
import urllib.request
from urllib.parse import urlencode, quote_plus
import json
import time 

from modules.common.module import BotModule

class PeerTubeClient:
    def __init__(self):
        self.instance_url = 'https://sepiasearch.org/'

    def search(self, search_string, count=0):
        if count == 0:
            count = 15 # Pt default, could also remove from params..
        params = urlencode({'search': search_string, 'count': count}, quote_via=quote_plus)
        search_url = self.instance_url + 'api/v1/search/videos?' + params
        response = urllib.request.urlopen(search_url)
        data = json.loads(response.read().decode("utf-8"))
        return data

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.instance_url = 'https://sepiasearch.org/'

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, ['ptall'])

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        if len(args) == 3:
            if args[1] == "setinstance":
                bot.must_be_owner(event)
                self.instance_url = args[2]
                bot.save_settings()
                await bot.send_text(room, 'Instance url set to ' + self.instance_url, bot_ignore=True)
                return

        if len(args) == 2:
            if args[1] == "showinstance":
                await bot.send_text(room, 'Using instance at ' + self.instance_url, bot_ignore=True)
                return

        if len(args) > 1:
            query = event.body[len(args[0])+1:]
            p = PeerTubeClient()
            p.instance_url = self.instance_url
            count = 1
            if args[0] == '!ptall':
                count = 0
            data = p.search(query, count)
            if len(data['data']) > 0:
                for video in data['data']:
                    video_url = video.get("url") or self.instance_url + 'videos/watch/' + video["uuid"]
                    duration = time.strftime('%H:%M:%S', time.gmtime(video["duration"]))
                    instancedata = video["account"]["host"]
                    html = f'<a href="{video_url}">{video["name"]}</a> {video["description"] or ""} [{duration}] @ {instancedata}'
                    text = f'{video_url} : {video["name"]} {video.get("description") or ""} [{duration}]'
                    await bot.send_html(room, html, text, bot_ignore=True)
            else:
                    await bot.send_text(room, 'Sorry, no videos found found.', bot_ignore=True)

        else:
            await bot.send_text(room, 'Usage: !pt <query> or !ptall <query> to return all results')

    def get_settings(self):
        data = super().get_settings()
        data['instance_url'] = self.instance_url
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("instance_url"):
            self.instance_url = data["instance_url"]

    def help(self):
        return ('PeerTube search')
