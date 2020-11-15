import sys
import traceback
from datetime import datetime, timedelta
from random import randrange

from igramscraper.exception.instagram_not_found_exception import \
    InstagramNotFoundException
from igramscraper.instagram import Instagram

from modules.common.pollingservice import PollingService


class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.instagram = Instagram()
        self.service_name = 'Instagram'
        self.enabled = False

    async def poll_implementation(self, bot, account, roomid, send_messages):
        try:
            medias = self.instagram.get_medias(account, 5)
            self.logger.info(f'Polling instagram account {account} for room {roomid} - got {len(medias)} posts.')
            for media in medias:
                if send_messages:
                    if media.identifier not in self.known_ids:
                        await bot.send_html(bot.get_room_by_id(roomid),
                                            f'<a href="{media.link}">Instagram {account}:</a> {media.caption}',
                                            f'{account}: {media.caption} {media.link}')
                self.known_ids.add(media.identifier)

        except InstagramNotFoundException:
            self.logger.error(f"{account} does not exist - deleting from room")
            self.account_rooms[roomid].remove(account)
            bot.save_settings()
        except Exception:
            self.logger.error('Polling instagram account failed:')
            traceback.print_exc(file=sys.stderr)

        polldelay = timedelta(minutes=30 + randrange(30))
        self.next_poll_time[roomid] = datetime.now() + polldelay
