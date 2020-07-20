from nio import RoomMessageUnknown, UnknownEvent

from modules.common.module import BotModule


class MatrixModule(BotModule):
    bot = None

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot
        bot.client.add_event_callback(self.unknownevent_cb, (UnknownEvent,))

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.unknownevent_cb)

    async def unknownevent_cb(self, room, event):
        try:
            if 'type' in event.source and event.source['type'] == 'im.vector.modular.widgets' and event.source['content']['type'] == 'jitsi':
                # Todo: Domain not found in Element Android events!
                domain = event.source['content']['data']['domain']
                conferenceId = event.source['content']['data']['conferenceId']
                isAudioOnly = event.source['content']['data']['isAudioOnly']
                sender = event.source['sender']
                sender_response = await self.bot.client.get_displayname(event.sender)
                sender = sender_response.displayname
                # This is just a guess - is this the proper way to generate URL? Probably not.
                jitsiUrl = f'https://{domain}/{conferenceId}'

                calltype = 'video call'
                if isAudioOnly:
                    calltype = 'audio call'

                plainMessage = f'{sender} started a {calltype}: {jitsiUrl}'
                htmlMessage = f'{sender} started a <a href="{jitsiUrl}">{calltype}</a>'
                await self.bot.send_html(room, htmlMessage, plainMessage)
        except Exception as e:
            self.logger.error(f"Failed parsing Jitsi event. Error: {e}")

    async def matrix_message(self, bot, room, event):
        pass

    def help(self):
        return 'Sends text links when user starts a Jitsi video or audio call in room'
