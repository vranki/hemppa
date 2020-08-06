from mastodon import Mastodon

from modules.common.module import BotModule


class MatrixModule(BotModule):
    apps = dict() # instance url <-> [app_id, app_secret]
    logins = dict() # mxid <-> [username, accesstoken, instanceurl]
    public = False

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) >= 1:
            if args[0] == "toot":
                if not self.public:
                    bot.must_be_owner(event)
                toot_body = " ".join(args[1:])
                if event.sender in self.logins.keys():
                    username = self.logins[event.sender][0]
                    accesstoken = self.logins[event.sender][1]
                    instanceurl = self.logins[event.sender][2]
                    toottodon = Mastodon(
                        access_token = accesstoken,
                        api_base_url = instanceurl
                    )
                    tootdict = toottodon.toot(toot_body)
                    print(tootdict)
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
                if not instanceurl in self.apps.keys():
                    app = Mastodon.create_app(f'Hemppa The Bot - {bot.client.user}', api_base_url = instanceurl)
                    self.apps[instanceurl] = [app[0], app[1]]
                    bot.save_settings()
                    await bot.send_text(room, f'Registered Mastodon app on {instanceurl}')

                mastodon = Mastodon(client_id = self.apps[instanceurl][0], client_secret = self.apps[instanceurl][1], api_base_url = instanceurl)
                access_token = mastodon.log_in(username, password)
                self.logins[mxid] = [username, access_token, instanceurl]
                bot.save_settings()
                await bot.send_text(room, f'Logged into {instanceurl} as {username}')
                return
        if len(args) == 1:
            if args[0] == "status":
                await bot.send_text(room, f'{len(self.logins)} users logged in, app registered on {len(self.apps)} instances, public use enabled: {self.public}')
            if args[0] == "logout":
                if event.sender in self.logins.keys():
                    # TODO: Is there a way to invalidate the access token with API?
                    del self.logins[event.sender]
                    bot.save_settings()
                    await bot.send_text(room, f'{event.sender} login data removed from the bot.')
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
 
    def get_settings(self):
        data = super().get_settings()
        data['apps'] = self.apps
        data['logins'] = self.logins
        data['public'] = self.public
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("apps"):
            self.apps = data["apps"]
        if data.get("logins"):
            self.logins = data["logins"]
        if data.get("public"):
            self.public = data["public"]

    def help(self):
        return ('Mastodon')
