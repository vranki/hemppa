from igramscraper.instagram import Instagram

class MatrixModule:
    instagram = Instagram()

    known_ids = set()
    first_run = True
    account_rooms = dict() # Roomid -> [account, account..]

    async def matrix_poll(self, bot, pollcount):
        if len(self.account_rooms):
            if pollcount % (6 * 60) == 0: # Poll every 60 min automatically
               await self.poll_all_accounts(bot)

    async def poll_all_accounts(self, bot):
        for roomid in self.account_rooms:
            accounts = self.account_rooms[roomid]
            for account in accounts:
                await self.poll_account(bot, account, roomid)

        self.first_run = False

    async def poll_account(self, bot, account, roomid):
        medias = self.instagram.get_medias(account, 5)

        for media in medias:
            if not self.first_run:
                if not media.identifier in self.known_ids:
                    await bot.send_html(bot.get_room_by_id(roomid), f'<a href="{media.link}">Instagram {account}:</a> {media.caption}', media.caption)

            self.known_ids.add(media.identifier)

    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args) == 2:
            if args[1] == 'list':
                await bot.send_text(room, f'Instagram accounts in this room: {self.account_rooms.get(room.room_id) or []}')
            elif args[1] == 'poll':
                bot.must_be_owner(event)
                await self.poll_all_accounts(bot)
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

                print(f'Accounts now for this room {self.account_rooms.get(room.room_id)}')

                bot.save_settings()
                await bot.send_text(room, 'Added new instagram account to this room')
            if args[1] == 'del':
                bot.must_be_admin(room, event)

                account = args[2]
                print(f'Removing account {account} from room id {room.room_id}')

                if self.account_rooms.get(room.room_id):
                    self.account_rooms[room.room_id].remove(account)

                print(f'Accounts now for this room {self.account_rooms.get(room.room_id)}')

                bot.save_settings()
                await bot.send_text(room, 'Removed instagram account from this room')

    def get_settings(self):
        return { 'account_rooms': self.account_rooms }

    def set_settings(self, data):
        if data.get('account_rooms'):
            self.account_rooms = data['account_rooms']

    def help(self):
        return('Instagram polling')
