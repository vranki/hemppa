# Hemppa - generic modular Matrix bot

This bot is meant to be super easy platform to write Matrix bot functionality
in Python. It uses matrix-nio library https://github.com/poljar/matrix-nio/ for
Matrix communications.

Zero configuration except minimal Matrix account info is needed. Everything else can
be done with bot commands.

Type !help in room with this bot running to list active modules.

If you don't want some modules, just delete the files from modules directory.

Support room: #hemppa:hacklab.fi - https://matrix.to/#/#hemppa:hacklab.fi

## Module list

### Bot

Bot management commands.

* !bot status - print bot status information
* !bot version - print version and uptime of the bot
* !bot quit - quit the bot process (Must be done as bot owner)
* !bot reload - reload all bot modules  (Must be done as bot owner)
* !bot stats - show statistics on matrix users seen by bot
* !bot leave - ask bot to leave this room (Must be done as admin in room)
* !bot modules - list all modules including enabled status
* !bot enable [module] - enable module (Must be done as admin in room)
* !bot disable [module] - disable module (Must be done as admin in room)

### Help

Prints help on existing modules.

### Echo

Simple example module that just echoes what user said.

* !echo Hello, world!

### Metar

Aviation weather metar service access.

* !metar eftp

### TAF

Aviation weather TAF service access.

* !taf eftp

### NOTAM

Aviation NOTAM data access. Currently supports only Finnish airports - implement other countries where
data is available.

* !notam efjm

### Teamup

Can access Teamup ( https://teamup.com/ ) calendar. Teamup has nice API and is easier to set up than Google so
prefer it if possible. This bot polls the calendar every 5 minutes and notifies the room of any changes.

Howto:

* Create a calendar in Teamup https://teamup.com/
* Get api key at https://teamup.com/api-keys/request
* !teamup apikey [your api key]
* !teamup add [calendar id]

Commands:

* !teamup apikey [apikey] - set api key (Must be done as bot owner)
* !teamup - list upcoming events in calendar
* !teamup add [calendar id] - add calendar to this room (Must be done as room admin)
* !teamup del [calendar id] - delete calendar from this room (Must be done as room admin)
* !teamup list - list calendars in this room
* !teamup poll - poll now for changes (Must be done as bot owner)

### Google Calendar

Can access a google calendar in a room. This is a bit pain to set up, sorry.

To set up, you'll need to generate oauth2 credentials.json file - see https://console.developers.google.com/apis/credentials

Run the bot on *local* machine as OAuth2 wants to open localhost url in your browser. I haven't found out an easy way to
do this on server.

There is a empty credentials.json file in the bot directory. Replace it with yours. When credentials.json is present, you must
authenticate the bot to access calendar. There will be a link in console like this:

``` text
Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=907....
```

Open the link and authenticate as needed. A new file token.pickle will be created in the directory and bot will read it in future.
Save the token.pickle and ship it with the bot to your server.

Now the bot should be usable.

Use !googlecal add [calendar id] to add new calendar to a room. The bot lists availble calendar ID's on startup and you can find them
in google calendar.

Commands:

* !googlecal - Show next 10 events in calendar
* !googlecal today - Show today's events
* !googlecal add [calendar id] - Add new calendar to room (Must be done as room admin)
* !googlecal del [calendar id] - Delete calendar from room (Must be done as room admin)
* !googlecal list - List calendars in this room

### Cron

Can schedule things to be done.

Commands:

* !cron daily [hour] [command] - Run command on start of hour (Must be done as room admin)
* !cron list - List commands in this room
* !cron clear - Clear command s in this room (Must be done as room admin)

Examples:

* !cron daily 19 "It is now 19 o clock"
* !cron daily 8 "!googlecal today"

### Location

Can search OpenStreetMaps for locations and send Matrix location events from them. Translates Matrix location events into OSM links.

Commands:

* !loc [location] - search for location

Example:

* !loc Tampere

### Slow polling services

These have the same usage - you can add one or more accounts to a room and bot polls the accounts.
New posts are sent to room.  Polls only randomly every 30 to 60 minutes to keep traffic at minimum.

Commands:

Prefix with selected service, for example "!ig add accountname" or "!twitter list"

* add [accountname] - Add account to this room (Must be done as room admin)
* del [accountname] - Delete account from room (Must be done as room admin)
* list - List accounts in room
* poll - Poll for new items  (Must be done as bot owner)
* clear - Clear all accounts from this room  (Must be done as room admin)
* debug - Show some debug information for accounts in room

#### Instagram

Polls instagram account(s). Uses instagram scraper library
without any authentication or api key.

See: https://github.com/realsirjoe/instagram-scraper/

#### Twitter

Polls twitter account(s). Uses twitter scraper library
without any authentication or api key.

See: https://github.com/taspinar/twitterscraper/tree/master/twitterscraper

#### Url

Watches all messages in a room and if a url is found tries to fetch it and
spit out the title if found. 

Defaults to off and needs to be activated on every room you want this.

Commands:

* !url status       - show current status
* !url title        - spam titles to room
* !url description  - spam descriptions
* !url both         - spam both title and description
* !url off          - stop spamming

Example:

* !url status

#### Cmd

Can be used to pre-configure shell commands run by bot. This is easy way to add
security issues to your bot so be careful.

Pre-defined commands can be set only by bot owner, but anyone can run them.
It's your responsibility as owner to make sure you don't allow running anything dangerous.

Commands have 5 second timeout so don't try to run long processes.

Environ variables seen by commands:

* MATRIX_USER: User who ran the command
* MATRIX_ROOM: Room the command was run (avoid using, may cause vulnerabilities)

Commands:

* !cmd run "command"         - Run command "command" (Must be done as bot owner)
* !cmd add cmdname "command" - Add new named command "command"  (Must be done as bot owner)
* !cmd remove cmdname        - Remove named command (Must be done as bot owner)
* !cmd list                  - List named commands
* !cmd cmdname               - Run a named command

Example:

* !cmd run "hostname"
* !cmd add systemstats "uname -a && uptime"
* !cmd systemstats
* !cmd add df "df -h"
* !cmd add whoami "echo You are $MATRIX_USER in room $MATRIX_ROOM."

## Bot setup

* Create a Matrix user
* Get user's access token - In Riot Web see Settings / Help & about

## Running on host

Run something like (tested on Ubuntu):

``` bash
sudo apt install python3-pip
sudo pip3 install pipenv
pipenv shell
pipenv install --pre
MATRIX_USER="@user:matrix.org" MATRIX_ACCESS_TOKEN="MDAxOGxvYlotofcharacters53CgYAYFgo" MATRIX_SERVER="https://matrix.org" JOIN_ON_INVITE=True BOT_OWNERS=@botowner:matrix.org
 python3 bot.py
```

## Running with Docker

Create .env file and set variables:

``` bash
MATRIX_USER=@user:matrix.org
MATRIX_ACCESS_TOKEN=MDAxOGxvYlotofcharacters53CgYAYFgo
MATRIX_SERVER=https://matrix.org
JOIN_ON_INVITE=True
BOT_OWNERS=@user1:matrix.org,@user2:matrix.org
DEBUG=False
```

Note: without quotes!

Just run:

``` bash
docker-compose up
```

## Env variables

`MATRIX_USER`, `MATRIX_ACCESS_TOKEN` and `MATRIX_SERVER` should be self-explanatory.
Set `JOIN_ON_INVITE` to anything if you want the bot to join invites automatically (do not set it if you don't want it to join).

You can get access token by logging in with Riot and looking from Settings / Help & About.

`BOT_OWNERS` is a comma-separated list of matrix id's for the owners of the bot.
Some commands require sender to be bot owner.
Typically set your own id into it.

__*ATTENTION:*__ Don't include bot itself in `BOT_OWNERS` if cron or any other module that can cause bot to send custom commands is used, as it could potentially be used to run owner commands as the bot itself.

To enable debugging for the root logger set `DEBUG=True`.

## Logging

Uses [python logging facility](https://docs.python.org/3/library/logging.html) to print information to the console. Customize it to your needs editing `config/logging.yml`.
See [logging.config documentation](https://docs.python.org/3/library/logging.config.html) for further information. 

## Module API

Just write a python file with desired command name and place it in modules. See current modules for
examples. No need to register it anywhere else.

*Simple skeleton for a bot module:*
```python

class MatrixModule(BotModule):
    
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        
        # Echo what they said back
        self.logger.debug(f"room: {room.name} sender: {event.sender} wants an echo")
        await bot.send_text(room, ' '.join(args))

    def help(self):
        return 'Echoes back what user has said'

``` 

Functions:

* matrix_start - Called once on startup
* async matrix_message - Called when a message is sent to room starting with !module_name
* matrix_stop - Called once before exit
* async matrix_poll - Called every 10 seconds
* help - Return one-liner help text
* get_settings - Must return a dict object that can be converted to JSON and sent to server
* set_settings - Load these settings. It should be the same JSON you returned in previous get_settings

You only need to implement the ones you need. See existing bots for examples.

Logging:

Use `self.logger` in your module to print information to the console.

Module settings are stored in Matrix account data.

If you write a new module, please make a PR if it's something useful for others.
