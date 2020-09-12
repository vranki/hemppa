from mastodon import Mastodon

from modules.common.module import BotModule


class MatrixModule(BotModule):
    apps = dict() # instance url <-> [app_id, app_secret]
    logins = dict() # mxid <-> [username, accesstoken, instanceurl]
    roomlogins = dict() # roomid <-> [username, accesstoken, instanceurl]
    public = False

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) >= 1:
            if args[0] == "toot":
                toot_body = " ".join(args[1:])
                accesstoken = None
                if room.room_id in self.roomlogins.keys():
                    bot.must_be_admin(room, event)
                    username = self.roomlogins[room.room_id][0]
                    accesstoken = self.roomlogins[room.room_id][1]
                    instanceurl = self.roomlogins[room.room_id][2]
                elif event.sender in self.logins.keys():
                    if not self.public:
                        bot.must_be_owner(event)
                    username = self.logins[event.sender][0]
                    accesstoken = self.logins[event.sender][1]
                    instanceurl = self.logins[event.sender][2]
                if accesstoken:
                    toottodon = Mastodon(
                        access_token = accesstoken,
                        api_base_url = instanceurl
                    )
                    tootdict = toottodon.toot(toot_body)
                    await bot.send_text(room, tootdict['url'])
                else:
                    await bot.send_text(room, f'{event.sender} has not logged in yet with the bot. Please do so.')
                return

        if len(args) == 4:
            if args[0] == "login":
                if not self.public:
                    bot.must_be_owner(event)
                mxid = event.sender
                instanceurl = args[1]
                username = args[2]
                password = args[3]
                await self.register_app_if_necessary(bot, room, instanceurl)
                await self.login_to_account(bot, room, mxid, None, instanceurl, username, password)
                return
        if len(args) == 5:
            if args[0] == "roomlogin":
                if not self.public:
                    bot.must_be_owner(event)
                roomalias = args[1]
                instanceurl = args[2]
                username = args[3]
                password = args[4]
                roomid = await bot.get_room_by_alias(roomalias)
                if roomid:
                    await self.register_app_if_necessary(bot, room, instanceurl)
                    await self.login_to_account(bot, room, None, roomid, instanceurl, username, password)
                else:
                    await bot.send_text(room, f'Unknown room alias {roomalias} - invite bot to the room first.')
                return
        if len(args) == 1:
            if args[0] == "status":
                out = f'App registered on {len(self.apps)} instances, public use enabled: {self.public}\n'
                out = out + f'{len(self.logins)} users logged in:\n'
                for login in self.logins.keys():
                    out = out + f' - {login} as {self.logins[login][0]} on {self.logins[login][2]}\n'
                out = out + f'{len(self.roomlogins)} per-room logins:\n'
                for roomlogin in self.roomlogins:
                    out = out + f' - {roomlogin} as {self.roomlogins[roomlogin][0]} on {self.roomlogins[roomlogin][2]}\n'

                await bot.send_text(room, out)
            if args[0] == "logout":
                if event.sender in self.logins.keys():
                    # TODO: Is there a way to invalidate the access token with API?
                    del self.logins[event.sender]
                    bot.save_settings()
                    await bot.send_text(room, f'{event.sender} login data removed from the bot.')
            if args[0] == "roomlogout":
                bot.must_be_admin(room, event)
                if room.room_id in self.roomlogins.keys():
                    del self.roomlogins[room.room_id]
                    bot.save_settings()
                    await bot.send_text(room, f'Login data for this room removed from the bot.')
                else:
                    await bot.send_text(room, f'No login found for room id {room.room_id}.')
            if args[0] == "clear":
                bot.must_be_owner(event)
                self.logins = dict()
                self.roomlogins = dict()
                bot.save_settings()
                await bot.send_text(room, f'All Mastodon logins cleared')
            if args[0] == "setpublic":
                bot.must_be_owner(event)
                self.public = True
                bot.save_settings()
                await bot.send_text(room, f'Mastodon usage is now public use')
            if args[0] == "setprivate":
                bot.must_be_owner(event)
                self.public = False
                bot.save_settings()
                await bot.send_text(room, f'Mastodon usage is now restricted to bot owners')

    async def register_app_if_necessary(self, bot, room, instanceurl):
        if not instanceurl in self.apps.keys():
            app = Mastodon.create_app(f'Hemppa The Bot - {bot.client.user}', api_base_url = instanceurl)
            self.apps[instanceurl] = [app[0], app[1]]
            bot.save_settings()
            await bot.send_text(room, f'Registered Mastodon app on {instanceurl}')

    async def login_to_account(self, bot, room, mxid, roomid, instanceurl, username, password):
        mastodon = Mastodon(client_id = self.apps[instanceurl][0], client_secret = self.apps[instanceurl][1], api_base_url = instanceurl)
        access_token = mastodon.log_in(username, password)
        print('login_To_account', mxid, roomid)
        if mxid:
            self.logins[mxid] = [username, access_token, instanceurl]
            await bot.send_text(room, f'Logged Matrix user {mxid} into {instanceurl} as {username}')
        elif roomid:
            self.roomlogins[roomid] = [username, access_token, instanceurl]
            await bot.send_text(room, f'Set room {roomid} Mastodon user to {username} on {instanceurl}')

        bot.save_settings()

    def get_settings(self):
        data = super().get_settings()
        data['apps'] = self.apps
        data['logins'] = self.logins
        data['roomlogins'] = self.roomlogins
        data['public'] = self.public
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("apps"):
            self.apps = data["apps"]
        if data.get("logins"):
            self.logins = data["logins"]
        if data.get("roomlogins"):
            self.roomlogins = data["roomlogins"]
        if data.get("public"):
            self.public = data["public"]

    def help(self):
        return ('Mastodon')
