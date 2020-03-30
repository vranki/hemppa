from datetime import datetime, timedelta
from random import randrange

from modules.common.module import BotModule


class PollingService(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.known_ids = set()
        self.account_rooms = dict()  # Roomid -> [account, account..]
        self.next_poll_time = dict()  # Roomid -> datetime, None = not polled yet
        self.service_name = "Service"
        self.poll_interval_min = 30  # TODO: Configurable
        self.poll_interval_random = 30
        self.owner_only = False # Set to true if service can be run only by bot owner
        self.send_all = False # Set to true to send all received items, even on first sync

    async def matrix_poll(self, bot, pollcount):
        if len(self.account_rooms):
            await self.poll_all_accounts(bot)

    async def poll_all_accounts(self, bot):
        now = datetime.now()
        delete_rooms = []
        for roomid in self.account_rooms:
            if roomid in bot.client.rooms:
                send_messages = True
                # First poll
                if not self.next_poll_time.get(roomid, None):
                    self.next_poll_time[roomid] = now + timedelta(hours=-1)
                    if not self.send_all:
                        send_messages = False
                        self.logger.debug(f'Polling all accounts for room {roomid} - but this is first sync so I wont send messages')
                if now >= self.next_poll_time.get(roomid):
                    accounts = self.account_rooms[roomid]
                    for account in accounts:
                        await self.poll_account(bot, account, roomid, send_messages)
            else:
                self.logger.warning(f'Bot is no longer in room {roomid} - deleting it from {self.service_name} room list')
                delete_rooms.append(roomid)
        for roomid in delete_rooms:
            self.account_rooms.pop(roomid, None)

        self.first_run = False

    async def poll_implementation(self, bot, account, roomid, send_messages):
        pass

    async def poll_account(self, bot, account, roomid, send_messages):
        polldelay = timedelta(minutes=self.poll_interval_min + randrange(self.poll_interval_random))
        self.next_poll_time[roomid] = datetime.now() + polldelay

        await self.poll_implementation(bot, account, roomid, send_messages)

    async def matrix_message(self, bot, room, event):
        if self.owner_only:
            bot.must_be_owner(event)

        args = event.body.split()

        if len(args) == 2:
            if args[1] == 'list':
                await bot.send_text(room,
                                    f'{self.service_name} accounts in this room: {self.account_rooms.get(room.room_id) or []}')
            elif args[1] == 'debug':
                await bot.send_text(room,
                                    f"{self.service_name} accounts: {self.account_rooms.get(room.room_id) or []} - known ids: {self.known_ids}\n" \
                                    f"Next poll in this room at {self.next_poll_time.get(room.room_id)} - in {self.next_poll_time.get(room.room_id) - datetime.now()}")
            elif args[1] == 'poll':
                bot.must_be_owner(event)
                self.logger.info(f'{self.service_name} force polling requested by {event.sender}')
                # Faking next poll times to force poll
                for roomid in self.account_rooms:
                    self.next_poll_time[roomid] = datetime.now() - timedelta(hours=1)
                await self.poll_all_accounts(bot)
            elif args[1] == 'clear':
                bot.must_be_admin(room, event)
                self.account_rooms[room.room_id] = []
                bot.save_settings()
                await bot.send_text(room, f'Cleared all {self.service_name} accounts from this room')
        if len(args) == 3:
            if args[1] == 'add':
                bot.must_be_admin(room, event)

                account = args[2]
                self.logger.info(f'Adding {self.service_name} account {account} to room id {room.room_id}')

                if self.account_rooms.get(room.room_id):
                    if account not in self.account_rooms[room.room_id]:
                        self.account_rooms[room.room_id].append(account)
                    else:
                        await bot.send_text(room, 'This account already added in this room!')
                        return
                else:
                    self.account_rooms[room.room_id] = [account]
                bot.save_settings()
                await bot.send_text(room, f'Added {self.service_name} account {account} to this room.')

            elif args[1] == 'del':
                bot.must_be_admin(room, event)

                account = args[2]
                self.logger.info(f'Removing {self.service_name} account {account} from room id {room.room_id}')

                if self.account_rooms.get(room.room_id):
                    self.account_rooms[room.room_id].remove(account)

                self.logger.info(f'{self.service_name} accounts now for this room {self.account_rooms.get(room.room_id)}')

                bot.save_settings()
                await bot.send_text(room, f'Removed {self.service_name} account from this room')

    def get_settings(self):
        data = super().get_settings()
        data['account_rooms'] = self.account_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('account_rooms'):
            self.account_rooms = data['account_rooms']

    def help(self):
        return f'{self.service_name} polling'
