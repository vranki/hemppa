#!/usr/bin/env python3

import asyncio
import glob
import importlib
import json
import os
import re
import sys
import traceback
import urllib.parse
import logging
from importlib import reload

import requests
from nio import AsyncClient, InviteEvent, JoinError, RoomMessageText, MatrixRoom, LogoutResponse, LogoutError, \
    LoginError


# Couple of custom exceptions


class CommandRequiresAdmin(Exception):
    pass


class CommandRequiresOwner(Exception):
    pass


class Bot:

    def __init__(self):
        self.appid = 'org.vranki.hemppa'
        self.version = '1.2'
        self.client = None
        self.join_on_invite = False
        self.modules = dict()
        self.pollcount = 0
        self.poll_task = None
        self.owners = []
        self.debug = os.getenv("DEBUG")

        self.initializeLogger()
        self.logger = logging.getLogger("hemppa")
        self.logger.debug("Initialized")

    def initializeLogger(self):
        log_format = '%(levelname)s - %(name)s - %(message)s'
        if self.debug:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

        logging.basicConfig(format=log_format)

    async def send_text(self, room, body):
        msg = {
            "body": body,
            "msgtype": "m.text"
        }
        await self.client.room_send(room.room_id, 'm.room.message', msg)

    async def send_html(self, room, html, plaintext):
        msg = {
            "msgtype": "m.text",
            "format": "org.matrix.custom.html",
            "formatted_body": html,
            "body": plaintext
        }
        await self.client.room_send(room.room_id, 'm.room.message', msg)

    def get_room_by_id(self, room_id):
        return self.client.rooms[room_id]

    # Throws exception if event sender is not a room admin
    def must_be_admin(self, room, event):
        if not self.is_admin(room, event):
            raise CommandRequiresAdmin

    # Throws exception if event sender is not a bot owner
    def must_be_owner(self, event):
        if not self.is_owner(event):
            raise CommandRequiresOwner

    # Returns true if event's sender is admin in the room event was sent in,
    # or is bot owner
    def is_admin(self, room, event):
        if self.is_owner(event):
            return True
        if event.sender not in room.power_levels.users:
            return False
        return room.power_levels.users[event.sender] >= 50

    # Returns true if event's sender is owner of the bot
    def is_owner(self, event):
        return event.sender in self.owners

    def save_settings(self):
        module_settings = dict()
        for modulename, moduleobject in self.modules.items():
            try:
                module_settings[modulename] = moduleobject.get_settings()
            except Exception:
                traceback.print_exc(file=sys.stderr)
        data = {self.appid: self.version, 'module_settings': module_settings}
        self.set_account_data(data)

    def load_settings(self, data):
        if not data:
            return
        if not data.get('module_settings'):
            return
        for modulename, moduleobject in self.modules.items():
            if data['module_settings'].get(modulename):
                try:
                    moduleobject.set_settings(
                        data['module_settings'][modulename])
                except Exception:
                    traceback.print_exc(file=sys.stderr)

    async def message_cb(self, room, event):
        # Figure out the command
        body = event.body
        if len(body) == 0:
            return
        if body[0] != '!':
            return

        command = body.split().pop(0)

        # Strip away non-alphanumeric characters, including leading ! for security
        command = re.sub(r'\W+', '', command)

        moduleobject = self.modules.get(command)

        if moduleobject is not None:
            if moduleobject.enabled:
                try:
                    await moduleobject.matrix_message(bot, room, event)
                except CommandRequiresAdmin:
                    await self.send_text(room, f'Sorry, you need admin power level in this room to run that command.')
                except CommandRequiresOwner:
                    await self.send_text(room, f'Sorry, only bot owner can run that command.')
                except Exception:
                    await self.send_text(room, f'Module {command} experienced difficulty: {sys.exc_info()[0]} - see log for details')
                    traceback.print_exc(file=sys.stderr)
        else:
            self.logger.error(f"Unknown command: {command}")
            await self.send_text(room, f"Sorry. I don't know what to do. Execute !help to get a list of available commands.")


    async def invite_cb(self, room, event):
        room: MatrixRoom
        event: InviteEvent

        if self.join_on_invite or self.is_owner(event):
            for attempt in range(3):
                result = await self.client.join(room.room_id)
                if type(result) == JoinError:
                    self.logger.error(f"Error joining room %s (attempt %d): %s", room.room_id, attempt, result.message)
                else:
                    self.logger.info(f"joining room '{room.display_name}'({room.room_id}) invited by '{event.sender}'")
                    break
        else:
            self.logger.warning(f'Received invite event, but not joining as sender is not owner or bot not configured to join on invite. {event}')

    def load_module(self, modulename):
        try:
            self.logger.info(f'load module: {modulename}')
            module = importlib.import_module('modules.' + modulename)
            module = reload(module)
            cls = getattr(module, 'MatrixModule')
            return cls(modulename)
        except ModuleNotFoundError:
            self.logger.error(f'Module {modulename} failed to load!')
            traceback.print_exc(file=sys.stderr)
            return None

    def reload_modules(self):
        for modulename in bot.modules:
            self.logger.info(f'Reloading {modulename} ..')
            self.modules[modulename] = self.load_module(modulename)

        self.load_settings(self.get_account_data())

    def get_modules(self):
        modulefiles = glob.glob('./modules/*.py')

        for modulefile in modulefiles:
            modulename = os.path.splitext(os.path.basename(modulefile))[0]
            moduleobject = self.load_module(modulename)
            if moduleobject:
                self.modules[modulename] = moduleobject

    def clear_modules(self):
        self.modules = dict()

    async def poll_timer(self):
        while True:
            self.pollcount = self.pollcount + 1
            for modulename, moduleobject in self.modules.items():
                if moduleobject.enabled:
                    try:
                        await moduleobject.matrix_poll(bot, self.pollcount)
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
            await asyncio.sleep(10)

    def set_account_data(self, data):
        userid = urllib.parse.quote(self.matrix_user)

        ad_url = f"{self.client.homeserver}/_matrix/client/r0/user/{userid}/account_data/{self.appid}?access_token={self.client.access_token}"

        response = requests.put(ad_url, json.dumps(data))
        self.__handle_error_response(response)

        if response.status_code != 200:
            self.logger.error('Setting account data failed. response: %s json: %s', response, response.json())

    def get_account_data(self):
        userid = urllib.parse.quote(self.matrix_user)

        ad_url = f"{self.client.homeserver}/_matrix/client/r0/user/{userid}/account_data/{self.appid}?access_token={self.client.access_token}"

        response = requests.get(ad_url)
        self.__handle_error_response(response)

        if response.status_code == 200:
            return response.json()
        self.logger.error(f'Getting account data failed: {response} {response.json()} - this is normal if you have not saved any settings yet.')
        return None

    def __handle_error_response(self, response):
        if response.status_code == 401:
            self.logger.error("access token is invalid or missing")
            self.logger.info("NOTE: check MATRIX_ACCESS_TOKEN or set MATRIX_PASSWORD")
            sys.exit(2)

    def init(self):

        self.matrix_user = os.getenv('MATRIX_USER')
        self.matrix_pass = os.getenv('MATRIX_PASSWORD')
        matrix_server = os.getenv('MATRIX_SERVER')
        bot_owners = os.getenv('BOT_OWNERS')
        access_token = os.getenv('MATRIX_ACCESS_TOKEN')
        join_on_invite = os.getenv('JOIN_ON_INVITE')

        if matrix_server and self.matrix_user and bot_owners:
            self.client = AsyncClient(matrix_server, self.matrix_user)
            self.client.access_token = access_token

            if self.client.access_token is None:
                if self.matrix_pass is None:
                    self.logger.error("Either MATRIX_ACCESS_TOKEN or MATRIX_PASSWORD need to be set")
                    sys.exit(1)

            self.join_on_invite = join_on_invite is not None
            self.owners = bot_owners.split(',')
            self.get_modules()

        else:
            self.logger.error("The environment variables MATRIX_SERVER, MATRIX_USER and BOT_OWNERS are mandatory")
            sys.exit(1)


    def start(self):
        self.load_settings(self.get_account_data())
        enabled_modules = [module for module_name, module in self.modules.items() if module.enabled]
        self.logger.info(f'Starting {len(enabled_modules)} modules..')
        for modulename, moduleobject in self.modules.items():
            if moduleobject.enabled:
                try:
                    moduleobject.matrix_start(bot)
                except Exception:
                    traceback.print_exc(file=sys.stderr)

    def stop(self):
        self.logger.info(f'Stopping {len(self.modules)} modules..')
        for modulename, moduleobject in self.modules.items():
            try:
                moduleobject.matrix_stop(bot)
            except Exception:
                traceback.print_exc(file=sys.stderr)

    async def run(self):
        if not self.client.access_token:
            login_response = await self.client.login(self.matrix_pass)

            if isinstance(login_response, LoginError):
                self.logger.error(f"Failed to login: {login_response.message}")
                return

            last_16 = self.client.access_token[-16:]
            self.logger.info(f"Logged in with password, access token: ...{last_16}")

        await self.client.sync()
        for roomid, room in self.client.rooms.items():
            self.logger.info(f"Bot is on '{room.display_name}'({roomid}) with {len(room.users)} users")
            if len(room.users) == 1:
                self.logger.info(f'Room {roomid} has no other users - leaving it.')
                self.logger.info(await self.client.room_leave(roomid))

        self.start()

        self.poll_task = asyncio.get_event_loop().create_task(self.poll_timer())

        if self.client.logged_in:
            self.load_settings(self.get_account_data())
            self.client.add_event_callback(self.message_cb, RoomMessageText)
            self.client.add_event_callback(self.invite_cb, (InviteEvent,))

            if self.join_on_invite:
                self.logger.info('Note: Bot will join rooms if invited')
            self.logger.info('Bot running as %s, owners %s', self.client.user, self.owners)
            self.bot_task = asyncio.create_task(self.client.sync_forever(timeout=30000))
            await self.bot_task
        else:
            self.logger.error('Client was not able to log in, check env variables!')

    async def shutdown(self):

        if self.client.logged_in:
            logout = await self.client.logout()

            if isinstance(logout, LogoutResponse):
                self.logger.info("Logout successful")
                try:
                    await self.client.close()
                    self.logger.info("Connection closed")
                except Exception as e:
                    self.logger.error("error while closing client: %s", e)

            else:
                logout: LogoutError
                self.logger.error(f"Logout unsuccessful. msg: {logout.message}")
        else:
            await self.client.client_session.close()


bot = Bot()
bot.init()
try:
    asyncio.get_event_loop().run_until_complete(bot.run())
except KeyboardInterrupt:
    if bot.poll_task:
        bot.poll_task.cancel()
    bot.bot_task.cancel()

bot.stop()
asyncio.get_event_loop().run_until_complete(bot.shutdown())
