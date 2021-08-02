from modules.common.module import BotModule
import random
import socket
from struct import pack, unpack
import time

# Modified from https://gist.github.com/azlux/315c924af4800ffbc2c91db3ab8a59bc

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.host = None
        self.port = 64738

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('host'):
            self.host = data['host']
        if data.get('port'):
            self.port = data['port']

    def get_settings(self):
        data = super().get_settings()
        data['host'] = self.host
        data['port'] = self.port
        return data

    async def matrix_message(self, bot, room, event):
        args = event.body.split()

        if len(args) > 1 and args[1] in ['set', 'setserver']:
            bot.must_be_owner(event)
            self.logger.info(f"room: {room.name} sender: {event.sender} is setting the server settings")
            if len(args) < 3:
                self.host = None
                return await bot.send_text(room, f'Usage: !{args[0]} {args[1]} [host] ([port])')
            self.host = args[2]
            if len(args) > 3:
                self.port = int(args[3])
            if not self.port:
                self.port = 64738
            bot.save_settings()
            return await bot.send_text(room, f'Set server settings: host: {self.host} port: {self.port}')

        self.logger.info(f"room: {room.name} sender: {event.sender} wants mumble info")
        if not self.host:
            return await bot.send_text(room, f'No mumble host info set!')

        try:
            ret = self.mumble_ping()
            # https://wiki.mumble.info/wiki/Protocol
            # [0,1,2,3] = version
            version = '.'.join(map(str, ret[1:4]))
            # [4] = identifier passed to the server (used here to get ping time)
            ping = int(time.time() * 1000) - ret[4]
            # [7] = bandwidth
            # [5] = users
            # [6] = max users
            await bot.send_text(room, f'{self.host}:{self.port} (v{version}): {ret[5]} / {ret[6]} (ping: {ping}ms)')
        except socket.gaierror as e:
            self.logger.error(f"room: {room.name}: mumble_ping failed: {e}")
            await bot.send_text(room, f'Could not get get mumble server info: {e}')

    def mumble_ping(self):
        addrinfo = socket.getaddrinfo(self.host, self.port, 0, 0, socket.SOL_UDP)

        for (family, socktype, proto, canonname, sockaddr) in addrinfo:
            s = socket.socket(family, socktype, proto=proto)
            s.settimeout(2)

            buf = pack(">iQ", 0, int(time.time() * 1000))
            try:
                s.sendto(buf, sockaddr)
            except (socket.gaierror, socket.timeout) as e:
                continue

            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                continue

            return unpack(">bbbbQiii", data)

    def help(self):
        return 'Show info about a mumble server'

    def long_help(self):
        text = self.help() + (
                '\n- "!mumble": Get the status of the configured mumble server')

        if bot and event and bot.is_owner(event):
            text += (
                    '\nOwner commands:'
                    '\n- "!mumble set [host] ([port])": Set use the following host and port'
                    '\n- If no port is given, defaults to 64738')
        return text
