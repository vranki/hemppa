from modules.common.module import BotModule
from nio import RoomMessageText

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.bridges = dict()
        self.bot = None
        self.enabled = False

    async def message_cb(self, room, event):
        if self.bot.should_ignore_event(event):
            return

        if event.body.startswith('!'):
            return

        source_id = None
        target_id = None

        for src_id, tgt_id in self.bridges.items():
            if room.room_id == src_id:
                source_id = src_id
                target_id = tgt_id
            elif room.room_id == tgt_id:
                source_id = tgt_id
                target_id = src_id

        if not source_id or not target_id:
            return

        target_room = self.bot.get_room_by_id(target_id)
        if(target_room):
            sendernick = target_room.user_name(event.sender)
            if not sendernick:
                sendernick = event.sender
            await self.bot.send_text(target_room, f'<{sendernick}> {event.body}', msgtype="m.text", bot_ignore=True)
        else:
            self.logger.warning(f"Bot doesn't seem to be in bridged room {target_id}")

    def matrix_start(self, bot):
        super().matrix_start(bot)
        bot.client.add_event_callback(self.message_cb, RoomMessageText)
        self.bot = bot

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.message_cb)
        self.bot = None

    async def matrix_message(self, bot, room, event):
        bot.must_be_admin(room, event)
        args = event.body.split()
        args.pop(0)
        if len(args) == 1:
            if args[0] == 'list':
                i = 1
                msg = f"Active relay bridges ({len(self.bridges)}):\n"
                for src_id, tgt_id in self.bridges.items():
                    srcroom = self.bot.get_room_by_id(src_id)
                    tgtroom = self.bot.get_room_by_id(tgt_id)

                    if srcroom:
                        srcroom = srcroom.display_name
                    else:
                        srcroom = f'??? {src_id}'

                    if tgtroom:
                        tgtroom = tgtroom.display_name
                    else:
                        tgtroom = f'??? {tgt_id}'

                    msg += f'{i}: {srcroom} <-> {tgtroom}'
                    i = i + 1
                await bot.send_text(room, msg)

        if len(args) == 2:
            if args[0] == 'bridge':
                roomid = args[1]
                room_to_bridge = bot.get_room_by_id(roomid)
                if room_to_bridge:
                    await bot.send_text(room, f'Bridging {room_to_bridge.display_name} here.')
                    self.bridges[room.room_id] = roomid
                    bot.save_settings()
                else:
                    await bot.send_text(room, f'I am not on room with id {roomid} (note: use id, not alias)!')
            elif args[0] == 'unbridge':
                idx = int(args[1]) - 1
                i = 0
                for src_id, tgt_id in self.bridges.items():
                    if i == idx:
                        del self.bridges[src_id]
                        await bot.send_text(room, f'Unbridged {src_id} and {tgt_id}.')
                        bot.save_settings()
                        return
                    i = i + 1

    def help(self):
        return 'Simple relaybot between two Matrix rooms'

    def get_settings(self):
        data = super().get_settings()
        data["bridges"] = self.bridges
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("bridges"):
            self.bridges = data["bridges"]
