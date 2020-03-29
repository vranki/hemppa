# Hemppa - generic modular Matrix bot

This bot is meant to be super easy platform to write Matrix bot functionality
in Python. It uses matrix-nio library https://github.com/poljar/matrix-nio/ for
Matrix communications.

Zero configuration except minimal Matrix account info is needed. Everything else can
be done with bot commands.

Type !help in room with this bot running to list active modules.

If you don't want some modules, just delete the files from modules directory.

Support room: #hemppa:hacklab.fi - https://matrix.to/#/#hemppa:hacklab.fi

## Hint: RSS Bridge

RSS Bridge is awesome project that creates RSS feeds for sites that don't have them:
https://github.com/RSS-Bridge/rss-bridge

If you want bot to notify on new posts on a service, check out if RSS Bridge
supports it! You can use the stock Matrix RSS bot to subscribe to feeds created
by RSS bridge.

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

You can choose to send titles as notices (as in Matrix spec) or normal
messages (IRC users might prefer this). This is a global setting currently.

Commands:

* !url status       - show current status
* !url title        - spam titles to room
* !url description  - spam descriptions
* !url both         - spam both title and description
* !url off          - stop spamming
* !url text         - send titles as normal text (must be owner)
* !url notice       - sends titles as notices (must be owner)

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

### Astronomy Picture of the Day

Upload and send latest astronomy picture of the day to the room.
See https://apod.nasa.gov/apod/astropix.html

Command:

* !apod - Sends latest Astronomy Picture of the Day to the room
* !apod YYYY-MM-DD - date of the APOD image to retrieve (ex. !apod 2020-03-15)
* !apod stats - show information about uri cache
* !apod clear - clear uri cache (Must be done as admin)
* !apod apikey [api-key] - set the nasa api key (Must be done as bot owner)
* !apod help - show command help

API Key:

The module uses a demo API Key which can be replaced by your own api key by setting the environment variable `APOD_API_KEY` or by setting the api key as a bot owner with command `!apod apikey [apikey]`. 

You can create one at https://api.nasa.gov/#signUp 

### Wolfram Alpha

Make queries to Wolfram Alpha

You'll need to get an appid from https://products.wolframalpha.com/simple-api/documentation/

Examples:

* !wa 1+1
* !wa airspeed of unladen swallow

Commands:

* !wa [query] - Query wolfram alpha
* !wa appid [appid] - Set appid (must be done as bot owner)

### Matrix Messaging API

This is a simple API to ask bot to send messages in Matrix using JSON file from external service.

You'll need an API endpoint (webserver) that contains a message queue. It must respond with following JSON to a HTTP GET request:

```json
{
   "messages":[
      {
         "to": "@example:matrix.org",
         "title": "Room Title",
         "message": "Hello from Hemppa"
      },
      {
         "to": "@another:matrix.user",
         "title": "Room 2 Title",
         "message": "Second message"
      }
   ]
}
```

Normally you want to clear the messages when the endpoint is GETted or the messages will repeat
every time bot updates itself.

These messages are sent to given Matrix users in private message with given room title.
Messages are sent "best effort" - if sending fails, it will be logged to bot output log.

Then just:
* !mxma add http://url.to.the/endpoint.json

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

`OWNERS_ONLY` is an optional variable once defined only the owners can operate the bot (this is a form of whitelisting)

__*ATTENTION:*__ Don't include bot itself in `BOT_OWNERS` if cron or any other module that can cause bot to send custom commands is used, as it could potentially be used to run owner commands as the bot itself.

To enable debugging for the root logger set `DEBUG=True`.

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

### Functions

* matrix_start - Called once on startup
* async matrix_message - Called when a message is sent to room starting with !module_name
* matrix_stop - Called once before exit
* async matrix_poll - Called every 10 seconds
* help - Return one-liner help text
* get_settings - Must return a dict object that can be converted to JSON and sent to server
* set_settings - Load these settings. It should be the same JSON you returned in previous get_settings

You only need to implement the ones you need. See existing bots for examples.

### Logging

Uses [python logging facility](https://docs.python.org/3/library/logging.html) to print information to the console. Customize it to your needs editing `config/logging.yml`.
See [logging.config documentation](https://docs.python.org/3/library/logging.config.html) for further information. 

Use `self.logger` in your module to print information to the console.

Module settings are stored in Matrix account data.

### Ignoring text messages

If you want to send a m.text message that bot should always ignore, set "org.vranki.hemppa.ignore" property in the event. Bot will ignore events with this set. 
Set the bot_ignore parameter to True in sender functions to acheive this.

If you write a module that installs a custom message handler, use bot.should_ignore_event(event) to check if event should be ignored.

## Contributing

If you write a new module, please make a PR if it's something useful for others.
