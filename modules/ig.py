from datetime import datetime, timedelta
from random import randrange

from igramscraper.exception.instagram_not_found_exception import \
    InstagramNotFoundException
from igramscraper.instagram import Instagram


class MatrixModule:
    instagram = Instagram()

    known_ids = set()
    account_rooms = dict()  # Roomid -> [account, account..]
    next_poll_time = dict()  # Roomid -> datetime, None = not polled yet

    async def matrix_poll(self, bot, pollcount):
        if len(self.account_rooms):
            await self.poll_all_accounts(bot)

    async def poll_all_accounts(self, bot):
        now = datetime.now()
        for roomid in self.account_rooms:
            send_messages = True
            if not self.next_poll_time.get(roomid, None):
                self.next_poll_time[roomid] = now
                send_messages = False
            if now >= self.next_poll_time.get(roomid):
                accounts = self.account_rooms[roomid]
                for account in accounts:
                    try:
                        await self.poll_account(bot, account, roomid, send_messages)
                    except InstagramNotFoundException:
                        print('ig error: there is ', account,
                              ' account that does not exist - deleting from room')
                        self.account_rooms[roomid].remove(account)
                        bot.save_settings()

        self.first_run = False

    async def poll_account(self, bot, account, roomid, send_messages):
        print('polling', account, roomid, send_messages)
        medias = self.instagram.get_medias(account, 5)

        for media in medias:
            if send_messages:
                if media.identifier not in self.known_ids:
                    await bot.send_html(bot.get_room_by_id(roomid), f'<a href="{media.link}">Instagram {account}:</a> {media.caption}', f'{account}: {media.caption} {media.link}')
            self.known_ids.add(media.identifier)
        polldelay = timedelta(minutes=30 + randrange(30))
        self.next_poll_time[roomid] = datetime.now() + polldelay

    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args) == 2:
            if args[1] == 'list':
                await bot.send_text(room, f'Instagram accounts in this room: {self.account_rooms.get(room.room_id) or []}')
            elif args[1] == 'poll':
                bot.must_be_owner(event)
                for roomid in self.account_rooms:
                    self.next_poll_time[roomid] = datetime.now()
                await self.poll_all_accounts(bot)
            elif args[1] == 'clear':
                bot.must_be_admin(room, event)
                self.account_rooms[room.room_id] = []
                bot.save_settings()
                await bot.send_text(room, 'Cleared all instagram accounts from this room')
        if len(args) == 3:
            if args[1] == 'add':
                bot.must_be_admin(room, event)

                account = args[2]
                print(f'Adding account {account} to room id {room.room_id}')

                if self.account_rooms.get(room.room_id):
                    if account not in self.account_rooms[room.room_id]:
                        self.account_rooms[room.room_id].append(account)
                    else:
                        await bot.send_text(room, 'This instagram account already added in this room!')
                        return
                else:
                    self.account_rooms[room.room_id] = [account]

                print(
                    f'Accounts now for this room {self.account_rooms.get(room.room_id)}')

                try:
                    await self.poll_account(bot, account, room.room_id, False)
                    bot.save_settings()
                    await bot.send_text(room, 'Added new instagram account to this room')
                except InstagramNotFoundException:
                    await bot.send_text(room, 'Account doesn\'t seem to exist')
                    self.account_rooms[room.room_id].remove(account)

            elif args[1] == 'del':
                bot.must_be_admin(room, event)

                account = args[2]
                print(
                    f'Removing account {account} from room id {room.room_id}')

                if self.account_rooms.get(room.room_id):
                    self.account_rooms[room.room_id].remove(account)

                print(
                    f'Accounts now for this room {self.account_rooms.get(room.room_id)}')

                bot.save_settings()
                await bot.send_text(room, 'Removed instagram account from this room')

    def get_settings(self):
        return {'account_rooms': self.account_rooms}

    def set_settings(self, data):
        if data.get('account_rooms'):
            self.account_rooms = data['account_rooms']

    def help(self):
        return('Instagram polling')
