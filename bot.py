import asyncio
import os
import json
from nio import (AsyncClient, RoomMessageText, RoomMessageUnknown, JoinError, InviteEvent)


class Bot:
    client = None
    join_on_invite = False

    async def send_html(self, body, client, room):
        msg = {
            "body": body,
            "msgtype": "m.text"
        }
        await self.client.room_send(self.get_room_id(room), 'm.room.message', msg)

    def get_room_id(self, room):
        for roomid in client.rooms:
            if self.client.rooms[roomid].named_room_name() == room.named_room_name():
                return roomid
        print('Cannot find id for room', room.named_room_name(), ' - is the bot on it?')
        return None

    async def message_cb(self, room, event):
        pass

    async def unknown_cb(self, room, event):
        if event.msgtype != 'm.location':
            return
        pass

    async def invite_cb(self, room, event):
        for attempt in range(3):
            result = await self.client.join(room.room_id)
            if type(result) == JoinError:
                print(f"Error joining room {room.room_id} (attempt %d): %s",
                    attempt, result.message,
                )
            else:
                break

    def init(self):
        self.client = AsyncClient(os.environ['MATRIX_SERVER'], os.environ['MATRIX_USER'])
        self.client.access_token = os.getenv('MATRIX_ACCESS_TOKEN')
        self.join_on_invite = os.getenv('JOIN_ON_INVITE')

    async def run(self):
        if not self.client.access_token:
            await self.client.login(os.environ['MATRIX_PASSWORD'])
            print("Logged in with password, access token:", client.access_token)

        await self.client.sync()

        if self.client.logged_in:
            self.client.add_event_callback(self.message_cb, RoomMessageText)
            self.client.add_event_callback(self.unknown_cb, RoomMessageUnknown)
            if self.join_on_invite:
                print('Note: Bot will join rooms if invited')
                self.client.add_event_callback(self.invite_cb, (InviteEvent,))
            print('Bot running')
            await self.client.sync_forever(timeout=30000)
        else:
            print('Client was not able to log in, check env variables!')


bot = Bot()
bot.init()

asyncio.get_event_loop().run_until_complete(bot.run())
