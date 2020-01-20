import traceback
import sys
from datetime import datetime, timedelta
from random import randrange

class PollingService:
    def __init__(self):
        self.known_ids = set()
        self.account_rooms = dict()  # Roomid -> [account, account..]
        self.next_poll_time = dict()  # Roomid -> datetime, None = not polled yet
        self.service_name = "Service" 

    async def matrix_poll(self, bot, pollcount):
        if len(self.account_rooms):
            await self.poll_all_accounts(bot)

    async def poll_all_accounts(self, bot):
        now = datetime.now()
        for roomid in self.account_rooms:
            send_messages = True
            # First poll
            if not self.next_poll_time.get(roomid, None):
                self.next_poll_time[roomid] = now + timedelta(hours=-1)
                send_messages = False
            if now >= self.next_poll_time.get(roomid):
                accounts = self.account_rooms[roomid]
                for account in accounts:
                    await self.poll_account(bot, account, roomid, send_messages)

        self.first_run = False

    async def poll_implementation(self, bot, account, roomid, send_messages):
        pass

    async def poll_account(self, bot, account, roomid, send_messages):
        polldelay = timedelta(minutes=30 + randrange(30))
        self.next_poll_time[roomid] = datetime.now() + polldelay

        await self.poll_implementation(bot, account, roomid, send_messages)


    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args) == 2:
            if args[1] == 'list':
                await bot.send_text(room, f'{self.service_name} accounts in this room: {self.account_rooms.get(room.room_id) or []}')
            if args[1] == 'debug':
                await bot.send_text(room, f"{self.service_name} accounts: {self.account_rooms.get(room.room_id) or []} - known ids: {self.known_ids}\n" \
                                          f"Next poll in this room at {self.next_poll_time.get(room.room_id)} - in {self.next_poll_time.get(room.room_id) - datetime.now()}")
            elif args[1] == 'poll':
                bot.must_be_owner(event)
                for roomid in self.account_rooms:
                    self.next_poll_time[roomid] = datetime.now()
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
                print(f'Adding {self.service_name} account {account} to room id {room.room_id}')

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
                print(
                    f'Removing {self.service_name} account {account} from room id {room.room_id}')

                if self.account_rooms.get(room.room_id):
                    self.account_rooms[room.room_id].remove(account)

                print(
                    f'{self.service_name} accounts now for this room {self.account_rooms.get(room.room_id)}')

                bot.save_settings()
                await bot.send_text(room, f'Removed {self.service_name} account from this room')

    def get_settings(self):
        return {'account_rooms': self.account_rooms}

    def set_settings(self, data):
        if data.get('account_rooms'):
            self.account_rooms = data['account_rooms']

    def help(self):
        return(f'{self.service_name} polling')
