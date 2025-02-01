import re

import requests

from .common.module import BotModule


# This module searches wikipedia for query, returns page summary and link.
class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.api_url = 'https://en.wikipedia.org/w/api.php'

    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args) > 1:
            query = event.body[len(args[0]) + 1:]
            try:
                response = requests.get(self.api_url, params={
                    'action': 'query',
                    'format': 'json',
                    'exintro': True,
                    'explaintext': True,
                    'prop': 'extracts',
                    'redirects': 1,
                    'titles': query,
                })

                response.raise_for_status()
                data = response.json()

                # Get the page id
                page_id = list(data['query']['pages'].keys())[0]

                if page_id == '-1':
                    await bot.send_text(room, 'No results found')
                    return

                # Get the page title
                title = data['query']['pages'][page_id]['title']

                # Get the page summary
                summary = data['query']['pages'][page_id]['extract']

                # Remove all html tags
                extract = re.sub('<[^<]+?>', '', summary)
                # Remove any multiple spaces
                extract = re.sub(' +', ' ', extract)
                # Remove any new lines
                extract = re.sub('', '', extract)
                # Remove any tabs
                extract = re.sub('\t', '', extract)

                # Truncate the extract, Element URL preview contains nonsense Wikipedia meta content
                if len(extract) <= 256:
                    pass
                else:
                    extract = ' '.join(extract[:256 + 1].split(' ')[0:-1]) + '...'

                # Get the page url
                url = f'https://en.wikipedia.org/wiki/{title}'

                # Convert all spaces to underscores in url
                url = re.sub(r'\s', '_', url)

                # Format the response
                response = f'{title}: {extract} \n{url}'

                # Send the response
                await bot.send_text(room, response)
                return
            except Exception as exc:
                await bot.send_text(room, str(exc))
        else:
            await bot.send_text(room, 'Usage: !wikipedia <query>')

    def help(self):
        return ('Wikipedia bot')