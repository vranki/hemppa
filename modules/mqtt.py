import re
import json
import paho.mqtt.client as mqtt

from nio import RoomMessageText
from modules.common.module import BotModule

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.forward_rooms = dict()        
        self.forward_clients = dict()

    def setup_forwarding(self, roomid, server, topic):
        forward = [roomid, server, topic]
        self.forward_rooms[roomid] = forward
        self.forward_clients[roomid] = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.forward_clients[roomid].connect(server)

    async def remove_forwarding(self, roomid):
        self.forward_clients[roomid].disconnect()
        del self.forward_rooms[roomid]

    async def matrix_poll(self, bot, pollcount):
        for mqttc in self.forward_clients.values():
            mqttc.loop(timeout=1.0)

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot
        bot.client.add_event_callback(self.text_cb, RoomMessageText)

    async def matrix_stop(self, bot):
        super().matrix_stop(bot)
        for mqttc in self.forward_clients:
            try:
                mqttc.disconnect()
            except:
                pass

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) == 4:
            if args[0] == "forward":
                bot.must_be_owner(event)
                roomalias = args[1]
                server = args[2]
                topic = args[3]
                roomid = await bot.get_room_by_alias(roomalias)
                if roomid:
                    if roomid in self.forward_rooms:
                        await bot.send_text(room, 'Room is already being forwarded!')
                        return
                    self.setup_forwarding(roomid, server, topic)
                    bot.save_settings()
                    await bot.send_text(room, 'Forwarding setup successfully!')
                else:
                    await bot.send_text(room, f'Unknown room alias {roomalias} - invite bot to the room first.')
                return
        if len(args) == 1:
            if args[0] == "status":
                bot.must_be_owner(event)
                out = f'Forwarding set up on {len(self.forward_rooms)} rooms:\n'
                for forward in self.forward_rooms.values():
                    out = out + f' - {forward[0]} -> {forward[1]} topic {forward[2]}\n'
                await bot.send_text(room, out)
                return

        if len(args) == 1:
            if args[0] == "clear":
                bot.must_be_owner(event)
                self.forward_rooms = dict()
                bot.save_settings()
                await bot.send_text(room, 'Cleared data')
                return

        if len(args) == 2:
            if args[0] == "remove":
                bot.must_be_owner(event)
                self.remove_forwarding(args[0])
                bot.save_settings()
                await bot.send_text(room, 'Forwarding removed')
                return

        await bot.send_text(room, 'Unknown command')

    async def text_cb(self, room, event):
        """
        Handle client callbacks for all room text events
        """
        if self.bot.should_ignore_event(event):
            return

        # no content at all?
        if len(event.body) < 1:
            return

        if room.room_id in self.forward_rooms.keys():
            forward = self.forward_rooms[room.room_id]
            if room.room_id in self.forward_clients:
                mqttc = self.forward_clients[room.room_id]
                mqttc.publish(forward[2], event.body)
            else:
                self.logger.debug('No client for room', room.room_id)

    def help(self):
        return 'Matrix->MQTT forwarder'

    def get_settings(self):
        data = super().get_settings()
        data['forward_rooms'] = self.forward_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if 'forward_rooms' in data:
            self.forward_rooms = data['forward_rooms']
        for roomid in self.forward_rooms.keys():
            forward = self.forward_rooms[roomid]
            self.setup_forwarding(forward[0], forward[1], forward[2])
