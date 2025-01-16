import urllib.request
import wolframalpha
from html import escape
import json
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
            short, full = self.parse_api_response(res)
            if full[0] and 'full' in args[0]:
                html, plain = full
            elif short[0]:
                html, plain = short
            else:
                plain = 'Could not find response for ' + query
                html = plain
            await bot.send_html(room, html, plain)
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

    def parse_api_response(self, res):
        """Parses the pods from wa and prepares texts to send to matrix

        :param res: the result from wolframalpha.Client
        :type res: dict
        :return: a tuple of tuples: ((primary_html, primary_plaintext), (full_html, full_plaintext))
        :rtype: tuple
        """
        htmls = []
        texts = []
        primary = None
        fallback = None

        pods = res.get('pod')
        if not pods:
            return (('<em>(data not available)</em>', '(data not available)'), ) * 2

        # workaround for bug(?) in upstream wa package
        if hasattr(pods, 'get'):
            pods = [pods]
        for pod in res['pod']:
            pod_htmls = []
            pod_texts = []
            spods = pod.get('subpod')
            if not spods:
                continue

            # workaround for bug(?) in upstream wa package
            if hasattr(spods, 'get'):
                spods = [spods]
            for spod in spods:
                title = spod.get('@title')
                text  = spod.get('plaintext')
                if not text:
                    continue

                if title:
                    html = f'<strong>{escape(title)}</strong>: {escape(text)}'
                    text = f'{title}: {text}'
                else:
                    html = escape(text)
                pod_htmls += html.split('\n')
                pod_texts += text.split('\n')

            if pod_texts:
                title = pod.get('@title')
                pod_html = '\n'.join([f'<p><strong>{escape(title)}</strong>\n<ul>']
                        + [f'<li>{s}</li>' for s in pod_htmls]
                        + ['</ul></p>'])
                pod_text = '\n'.join([title]
                        + [f'- {s}' for s in pod_texts])
                htmls.append(pod_html)
                texts.append(pod_text)
                if not primary and self.is_primary(pod):
                    primary = (f'<strong>{escape(title)}</strong>: ' + ' | '.join(pod_htmls),
                               f'{title}: ' + ' | '.join(pod_texts))
                else:
                    fallback = fallback or (' | '.join(pod_htmls), ' | '.join(pod_texts))

        return (primary or fallback, ('\n'.join(htmls), '\n'.join(texts)))

    def is_primary(self, pod):
        return pod.get('@primary') or 'Definition' in pod.get('@title') or 'Result' in pod.get('@title')

    def help(self):
        return ('Wolfram Alpha search')

    def long_help(self, bot=None, event=None, **kwargs):
        text = self.help() + (
            '\n- "!wa [query]": Query WolframAlpha and return the primary pod'
            '\n- "!wafull [query]": Query WolframAlpha and return all pods'
            )
        if bot and event and bot.is_owner(event):
            text += '\n- "!wa appid [appid]": Set appid'
        return text
