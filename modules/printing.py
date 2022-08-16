from modules.common.module import BotModule
from nio import RoomMessageMedia
from typing import Optional
import sys
import traceback
import cups
import httpx
import aiofiles
import os

# Credit: https://medium.com/swlh/how-to-boost-your-python-apps-using-httpx-and-asynchronous-calls-9cfe6f63d6ad
async def download_file(url: str, filename: Optional[str] = None) -> str:
    filename = filename or url.split("/")[-1]
    filename = f"/tmp/{filename}"
    client = httpx.AsyncClient()
    async with client.stream("GET", url) as resp:
        resp.raise_for_status()
        async with aiofiles.open(filename, "wb") as f:
            async for data in resp.aiter_bytes():
                if data:
                    await f.write(data)
    await client.aclose()
    return filename

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.printers = dict() # roomid <-> printername
        self.bot = None
        self.paper_size = 'A4' # Todo: configurable
        self.enabled = False

    async def file_cb(self, room, event):
        try:
            if self.bot.should_ignore_event(event):
                return
            if room.room_id in self.printers:
                printer = self.printers[room.room_id]
                self.logger.debug(f'RX file - MXC {event.url} - from {event.sender}')
                https_url = await self.bot.client.mxc_to_http(event.url)
                self.logger.debug(f'HTTPS URL {https_url}')
                filename = await download_file(https_url)
                self.logger.debug(f'RX filename {filename}')
                conn = cups.Connection ()
                conn.printFile(printer, filename, f"Printed from Matrix - {filename}", {'fit-to-page': 'TRUE', 'PageSize': self.paper_size})
                await self.bot.send_text(room, f'Printing file on {printer}..')
                os.remove(filename) # Not sure if we should wait first?
            else:
                self.logger.debug(f'No printer configured for room {room.room_id}')
        except:
                self.logger.warning(f"File callback failure")
                traceback.print_exc(file=sys.stderr)
                await self.bot.send_text(room, f'Printing failed, sorry. See log for details.')

    def matrix_start(self, bot):
        super().matrix_start(bot)
        bot.client.add_event_callback(self.file_cb, RoomMessageMedia)
        self.bot = bot

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.file_cb)
        self.bot = None

    async def matrix_message(self, bot, room, event):
        bot.must_be_owner(event)
        args = event.body.split()
        args.pop(0)
        conn = cups.Connection ()
        printers = conn.getPrinters ()

        if len(args) == 1:
            if args[0] == 'list':
                msg = f"Available printers:\n"
                for printer in printers:
                    print(printer, printers[printer]["device-uri"])
                    msg += f' - {printer}  /  {printers[printer]["device-uri"]}'
                    for roomid, printerid in self.printers.items():
                        if printerid == printer:
                            msg += f' <- room {roomid}'
                    msg += '\n'
                await bot.send_text(room, msg)
            elif args[0] == 'rmroomprinter':
                del self.printers[room.room_id]
                await bot.send_text(room, f'Deleted printer from this room.')
                bot.save_settings()

        if len(args) == 2:
            if args[0] == 'setroomprinter':
                printer = args[1]
                if printer in printers:
                    await bot.send_text(room, f'Printing with {printer} here.')
                    self.printers[room.room_id] = printer
                    bot.save_settings()
                else:
                    await bot.send_text(room, f'No printer called {printer} in your CUPS.')
            if args[0] == 'setpapersize':
                self.paper_size = args[1]
                bot.save_settings()
                await bot.send_text(room, f'Paper size set to {self.paper_size}.')

    def help(self):
        return 'Print files from Matrix'

    def get_settings(self):
        data = super().get_settings()
        data["printers"] = self.printers
        data["paper_size"] = self.paper_size
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("printers"):
            self.printers = data["printers"]
        if data.get("paper_size"):
            self.paper_size = data["paper_size"]
