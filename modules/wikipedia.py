import re
import html

import requests

from modules.common.module import BotModule

# This module searches wikipedia for query, returns page summary and link.
class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.api_url = 'https://en.wikipedia.org/w/api.php'

    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args) == 3 and args[1] == 'apikey':
            bot.must_be_owner(event)
            self.api_key = args[2]
            bot.save_settings()
            await bot.send_text(room, 'Api key set')
        elif len(args) > 1:
            query = event.body[len(args[0])+1:]
            try:
                response = requests.get(self.api_url, params={
                    'action': 'query',
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'titles': query,
                    'format': 'json',
                    'formatversion': 2
                })

                response.raise_for_status()
                data = response.json()
                if 'query' not in data or 'pages' not in data['query'] or len(data['query']['pages']) == 0:
                    await bot.send_text(room, 'No results found')
                    return

                page = data['query']['pages'][0]

                if 'extract' not in page:
                    await bot.send_text(room, 'No results found')
                    return

                # Remove all html tags
                extract = re.sub('<[^<]+?>', '', page['extract'])
                # Remove any multiple spaces
                extract = re.sub(' +', ' ', extract)
                # Remove any new lines
                extract = re.sub('', '', extract)
                # Remove any tabs
                extract = re.sub('\t', '', extract)

                # Truncate to 500 chars
                extract = extract[:500]

                # Add a link to the page
                extract = extract + '\nhttps://en.wikipedia.org/?curid=' + str(page['pageid'])

                await bot.send_text(room, extract)
                return
            except Exception as exc:
                await bot.send_text(room, str(exc))
        else:
            await bot.send_text(room, 'Usage: !wikipedia <query>')

    def help(self):
        return ('Wikipedia bot')

    def get_settings(self):
        data = super().get_settings()
        data["api_key"] = self.api_key
        return data