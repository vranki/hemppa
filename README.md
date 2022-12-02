# Hemppa - generic modular Matrix bot

This bot is meant to be super easy platform to write Matrix bot functionality
in Python. It uses matrix-nio library https://github.com/poljar/matrix-nio/ for
Matrix communications.

Zero configuration except Matrix account info is needed. Everything else can
be done with bot commands.

Type !help in room with this bot running to list active modules.

If you don't want some modules, just delete the files from modules directory or
disable them with !bot disable command.

End-to-end encryption is currently not supported by bot but should be doable.
Bot won't respond to commands in e2ee rooms. PR for enabling e2ee is welcome!

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
* !bot ping - print the ping time between the server and the bot
* !bot version - print version and uptime of the bot
* !bot stats - show statistics on matrix users seen by bot

The following must be done as the bot owner:

* !bot enable [module] - enable module
* !bot disable [module] - disable module
* !bot quit - quit the bot process
* !bot reload - reload all bot modules
* !bot export - export all bot settings as json
* !bot export [module] - export a module's settings as json
* !bot import [json object] - Update all bot settings from json
* !bot import [module] [json object] - Update a module's settings from json
* !bot import [module] [key ...] [json object] - Update a sub-object in a module from json
  * Example: !bot import alias aliases {"osm": "loc", "sh": "cmd"}
* !bot logs [module] ([count]) - Print the [count] most recent messages the given module has reported
* !bot uricache (view|clean|clear) - View the uri cache, or clear it.
The uri cache prevents the bot from uploading a blob from a url repeatedly
* !bot leave - ask bot to leave this room
* !bot modules - list all modules including enabled status
* !bot rooms - list rooms the bot is on

### Help

Prints help on existing modules.

* !help - get short help for all currently-enabled modules
* !help [module] - get long help for the given module, or short help if unavailable
* !sethelp msg (on|yes|1) - Configure !help to respond to !help requests via a direct message, instead of in the current room
(Must be done as bot owner)

### Alias

Add or remove aliases for a module.

* !alias list - List all aliases
* !alias add [newname] [module] - Define an alias for [module] (Must be done as bot owner)
* !alias remove [name] - Remove [name] as an alias (Must be done as bot owner)

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

NOTE: disabled by default

### Cron

Can schedule things to be done.

Commands:

* !cron daily [hour] [command] - Run command on start of hour (Must be done as room admin)
* !cron list - List commands in this room
* !cron clear - Clear command s in this room (Must be done as room admin)
* !cron time - Print the current datetime and time zone that the cron command will use (time zone set using the `TZ` environment variable)

Examples:

* !cron daily 19 "It is now 19 o clock"
* !cron daily 8 "!googlecal today"

### Location

Can search OpenStreetMaps for locations and send Matrix location events from them. Translates Matrix location events into OSM links.

Commands:

* !loc [location] - search for location
* !loc enable     - enable location to link translation in this room (must be done as room admin)
* !loc disable    - disable location to link translation in this room (must be done as room admin)

Example:

* !loc Tampere

### Room

This module is for interacting with the room that the commands are being executed on.

* !room servers                                     Lists the servers in the room
* !room joined                                      Responds with the joined members count
* !room banned                                      Lists the banned users and their provided reason
* !room kicked                                      Lists the kicked users and their provided reason
* !room state [event type] [optional state key]     Gets a state event with given event type and optional state key
* !room tombstone [target]                          Creates a tombstone event pointing to target room. Target room can be alias (starting with #) or id (starting with !). User must be admin in the room.

Note on tombstone: If using alias, bot must be present in target room. This is the preferred way. If using id, make sure it's correct, as it's not validated!
Tombstoning requires power level for room upgrade. Make sure bot has it in the room.

### Welcome to Room

When configured in a room, the bot will monitor a room for new users and send new users a welcome message 1:1. It will then notify bot owners of the new user. It will also, optionally, notify of user departure.

Commands:

* !welcome_room welcome_message [message]        Sets the welcome message, along with other variables needed to detect new users.
* !welcome_room notify_departure [True/False]    Sets whether bot owners will be notified of departure from room. Defaults to False.
* !welcome_room settings                         Shows the current settings for the welcome_room module.

### Welcome to Server

As a server admin, the bot will monitor new user creation on the server and send the welcome message to new users 1:1. It will then notify bot owners of the new user.

Commands:

* !welcome_server welcome_message [message]    Sets the welcome message, along with other variables needed to detect new users.
* !welcome_server settings                     Shows current settings for the welcome_server module

### Slow polling services

These have the same usage - you can add one or more accounts to a room and bot polls the accounts.
New posts are sent to room.  Polls only randomly every 30 to 60 minutes to keep traffic at minimum.

Commands:

Prefix with selected service, for example "!ig add accountname" or "!teamup list"

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

NOTE: disabled by default

#### Matrix Messaging API (mxma)

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

mxma requires all commands to be run as bot owner.

#### SpaceAPI

Polls the status of Hack- and Makerspaces that provide an endpoint
that conforms to the [SpaceAPI](https://spaceapi.io/) protocol and notifies 
about changes of the opening status.

To add a new endpoint simply use 
`!spaceapi add https://hackspace.example.org/status`

For Admins: A template and I18N can be configured via settings of 
the module. Use `!bot export spacepi`, then change the 
settings and import again with `!bot import spacepi SETTINGS`.

### Url

Watches all messages in a room and if a url is found tries to fetch it and
spit out the title if found.

Defaults to off and needs to be activated on every room you want this.

You can choose to send titles as notices (as in Matrix spec) or normal
messages (IRC users might prefer this). This is a global setting currently.
You can set a blacklist to ignore URLs containing words from the blacklist.

Commands:

* !url status          - show current status
* !url title           - spam titles to room
* !url description     - spam descriptions
* !url both            - spam both title and description
* !url off             - stop spamming
* !url text            - send titles as normal text (must be owner)
* !url notice          - sends titles as notices (must be owner)
* !url blacklist list  - blacklist comma separated list of url substrings
* !url blacklist clear - clear blacklist

Example:

* !url status
* !url blacklist www.youtube.com,www.somethingelse.com

NOTE: Disabled by default, i.e. you also need to enable it before activating it

### Cmd

Can be used to pre-configure shell commands run by bot. This is easy way to add
security issues to your bot so be careful.

Pre-defined commands can be set only by bot owner, but anyone can run them.
It's your responsibility as owner to make sure you don't allow running anything dangerous.

Commands have 5 second timeout so don't try to run long processes.

Environ variables seen by commands:

* MATRIX_USER: User who ran the command
* MATRIX_ROOM: Room the command was run (avoid using, may cause vulnerabilities)

Commands:

* !cmd run command              - Run command "command" (Must be done as bot owner)
* !cmd add "cmdname" command    - Add new named command "command"  (Must be done as bot owner)
* !cmd remove "cmdname"         - Remove named command (Must be done as bot owner)
* !cmd list                     - List named commands
* !cmd "cmdname"                - Run a named command

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
* !apod avatar (YYYY-MM-DD) - additionally, set roomavatar to the astronomy pic of the day (ignored if not admin in room)

API Key:

The module uses a demo API Key which can be replaced by your own api key by setting the environment variable `APOD_API_KEY` or by setting the api key as a bot owner with command `!apod apikey [apikey]`.

You can create one at https://api.nasa.gov/#signUp


### Inspirobot

Query a randomly generated inspirational poster from https://inspirobot.me/ upload and send to the room.

Command:

* !inspire - Generate inspiration and post to the room
* !inspire help - Show this help


### Wolfram Alpha

Make queries to Wolfram Alpha

You'll need to get an appid from https://products.wolframalpha.com/simple-api/documentation/

Examples:

* !wa 1+1
* !wafull airspeed of unladen swallow

Commands:

* !wa [query] - Query wolfram alpha and return the primary pod.
* !wafull [query] - Query wolfram alpha and return all pods.
* !wa appid [appid] - Set appid (must be done as bot owner)

### OGN Field Log (FLOG)

Open Glider Network maintains a unified tracking platform for gliders, drones and other aircraft.

Read more about OGN at https://www.glidernet.org/

FLOG module supports showing field logs for OGN receivers and can display live
field log in a room. It can also show latest known location of an aircraft
using !sar command.

It uses FlightBook instance at https://flightbook.glidernet.org/

FlightBook sources and documentation at https://gitlab.com/lemoidului/ogn-flightbook


Real life field log output looks something like:

```
Flights at Chateau Arnoux St Auban (LFMX) 2021-04-09:
13:36-18:01 04:24 F-CLDG JS-3 18M FM 2291m
13:46-··:··       F-CIFF Arcus T FP
13:57-17:13 03:15 JS-1 C21 72 2636m
14:08-17:30 03:22 ZS-GCC JS-1 C21 FD 2754m
18:29-··:··       F-CLDG JS-3 18M FM
```

Commands and examples:

(You must be room admin for all commands)

* !flog station EFJM - set the default station to track for this room
* !flog rmstation - remove station from this room
* !flog - Show field flog for the room's station (can be used by any user)
* !flog EFJM - Show field flog for any station (can be used by any user)
* !flog status - print status of this room
* !flog live - enable live field log for this room
* !flog rmlive - disable live field log for this room
* !sar OH-123 - Send latest known location of aircraft OH-123

NOTE: disabled by default

### Jitsi

If enabled, Jitsi calls created with Matrix clients will be sent as text messages
to rooms, allowing non-matrix users to join them.

### Mastodon

Send toots to Mastodon. You can login to Mastodon with the bot and toot with it.

Normal login is personal - it's mapped to your Matrix ID.

Room login overrides personal login and allows room admins to toot to a specified account.

You can limit usage to bot owners only or make it public.

Note: You can subscribe to Mastodon users and hashtags with stock RSS feed integration.
Mastodon generates the feeds automatically!

Commands:

* !md status - print status of mastodon module
* !md login [instanceurl] [e-mail] [password] - log in your Matrix user to Mastodon instance (do in private chat!)
* !md toot [toot] - send a toot message. If said in a room with per-room login, user must be a admin in the room.
* !md logout - log out the user from the bot
* !md roomlogin [room] [instanceurl] [e-mail] [password] - same as login but assigns a per-room mastodon account  (do in private chat!)
* !md roomlogout - Say in a room that has per-room login. This will remove the login. Must be room admin.
* !md setpublic - ANY user can use login command to login and use the Mastodon module (must be done as bot owner)
* !md setprivate - Only bot owners can use Mastodon module (default) (must be done as bot owner)
* !md clear - Clear all logins from the bot

Example commands:

* !md login https://my.instance/ me@email.invalid r00tm3
* !md roomlogin #myroom:matrix.org https://my.instance/ me@email.invalid r00tm3

### Relay bridge

Bridges two or more Matrix rooms together via relaybot.

Note: Room ID is not same as room alias! Rooms can exist without aliases so ID's are more flexible. Room id is usually in format !123LotOfRandomChars:server.org

To get room ID, it's in Element Web room settings | Advanced | Internal room ID

Before bridging the bot must be present on both rooms.

Commands:

* !relay bridge [roomid] - Bridge room with given ID to this room (must be done as bot owner)
* !relay list - List bridged rooms (and their index numbers) (must be done as bot owner)
* !relay unbridge [number] - Remove the given bridge number (must be done as bot owner)

File uploads, joins, leaves or other special events are not (yet) handled. Contributions welcome.

Relaybots are stupid. Please prefer real Matrix bridges to this. Sometimes there's no alternative.

### Printing

With this module you can set up a room to print any uploaded files on a specified printer.
The printer must be visible to bot via CUPS.

Commands (all can be done by bot owner only):

* !printing list - Lists available printers and their rooms
* !printing setroomprinter [printername] - Assignes given printer to this room
* !printing rmroomprinter - Deletes printer from this room
* !printing setpapersize [papersize] - Set global paper size. Default is A4. See printer settings for valid values.

The module sends the files to CUPS for printing so please see CUPS documentation
on what works and what doesn't.

Tested formats: PDF, JPG, PNG

SVG files are printed as text currently, avoid printing them.

This module is disabled by default.

### Giphy

Can be used to post a picture from giphy given a query string.

API Key:

The module has no API Key set up by default. You have to provide an api key by using the relevant command.

Read the documentation to create one at https://developers.giphy.com/docs/api

Commands:

* !giphy apikey [apikey]    - Set api key (Must be done as bot owner)
* !giphy [query]            - Post the first image result from giphy for the given [query]  
  

Example:

* !giphy test

### Gfycat

NOTE: This module is not working at the moment - gfycat now needs API key

Can be used to post a picture from Gfycat given a query string.

Commands:

* !gfycat [query]   - Post the first image result from gfycat for the given [query]  

Example:

* !gfycat test

### Tautulli

Can be used to fetch recently added information from Tautulli or receive Tautulli recently added notification webhook

Commands:

* !tautulli apikey [apikey]             - Set api key (Must be done as bot owner)
* !tautulli movie                       - Show the last 10 recently added movies to Plex library monitered by Tautulli
* !tautulli show                        - Show the last 10 recently added tv series epsiodes to Plex library monitered by Tautulli
* !tautulli artist                      - Show the last 10 recently added music artists to Plex library monitered by Tautulli
* !tautulli add [room_id] encrypted     - Add the provided encrypted [room_id] to the list of rooms to post the recently added notifications received by the webhook
* !tautulli add [room_id] plain         - Add the provided unencrypted [room_id] to the list of rooms to post the recently added notifications received by the webhook
* !tautulli remove [room_id] encrypted  - Remove the provided encrypted [room_id] to the list of rooms to post the recently added notifications received by the webhook
* !tautulli remove [room_id] plain      - Remove the provided unencrypted [room_id] to the list of rooms to post the recently added notifications received by the webhook

Tautulli instance and API Key:

The module work with an instance of Tautulli accessible on URL defined by env variable `TAUTULLI_URL`
In order to load art pictures you need to define an instance of Plex Media Server with its token as well by the two env variables `PLEX_MEDIA_SERVER_URL` and `PLEX_MEDIA_SERVER_TOKEN`
You have to provide an api key by using the relevant command.

Environ variables seen by command:

* PLEX_MEDIA_SERVER_URL: Url accessible from the machine to an instance of Plex Media Server
* PLEX_MEDIA_SERVER_TOKEN: Plex Token for the instance of Plex Media Server
* TAUTULLI_URL: Url accessible from the machine to an instance of Tautulli
* TAUTULLI_NOTIFIER_ADDR: Listening address for the Tautulli webhook handler target
* TAUTULLI_NOTIFIER_PORT: Listening port for the Tautulli webhook handler target
* BOT_OWNERS: Owner of the rooms in the list for the notification webhook

Docker environment:

Since the module needs access to the source of the running Tautulli instance volumes on both Docker (hemppa and Tautulli) should be defined and being visible each other.
When running on Docker the env variables seen by command should be defined for the bot instance. 

Example:

* !tautulli movie
* !tautulli add !OGEhHVWSdvArJzumhm:matrix.org plain
* !tautulli remove !OGEhHVWSdvArJzumhm:matrix.org plain

### Github based asset management

This module was written for asset (machines, tasks and todo) management by
mis-using GitHub issues and labels. It has been designed to be used with hackerspace
environment but can be extended to any purpose.

#### Github project setup

* Create labels to github that represent for example different machines and spaces.
You can create any number of them.
* Define label colors for each type of asset. These are called domains in this module. 
For example set all machine labels to be #B60205 and space labels to be #0E8A16. These 
can be easily picked from color chooser.
* Edit the repository description and add a json block describing the
label domains and their colors (array format supports multiple colors per domain). For example:

```
Hackerspace machines, todo and stuff. domains={"koneet":["#BFDADC","#0CBBF0","#0CBBF0","#E15D19","#ED49CF"],"tilat":["#0E8A16","#1E8A16"]}
```

Make sure you type the description on one line - this is a silly Github limitation.

* When creating issues, assign machine and/or space labels for them.
For example, if a wood lathe is broken, create issue with labels
"Wood lathe" and "Wood working room".

#### Usage

* !ghproj setrepo [repository] - Set repository for this room (room admin only)
* !ghproj repo - Shows which repository this room tracks
* !ghproj rmrepo - Remove repository from this room (room admin only)
* !ghproj [domain] - List machine statuses in this domain

Repository name must be in format TampereHacklab/Inventaario - you can
use this as a example to see how the labels work.

### PeerTube search

Searches PeerTube instances for videos. Uses Sepia Serch at https://sepiasearch.org/
by default, but you can set any single instance to search on.

#### Usage

* !pt [query]           - Search for exactly one video matching query
* !ptall [query]        - Search up to 15 videos matching query
* !pt setinstance [url] - Set instance url, must end with / (example: https://peertube.cpy.re/)
* !pt showinstance      - Print which instance is used

### User management

Admin commands to manage users and some utilities.

You can classify users based on MXID to get stats on where users come from.

#### Usage

* !users list [pattern]  - List users matching wildcard pattern in this room (must be owner)
* !users listall [pattern]  - List users matching wildcard pattern globally (must be owner)
* !users kick [pattern]  - Kick users matching wildcard pattern from room (must be admin in room)
* !users classify add [name] [pattern] - Add a classification pattern (must be owner)
* !users classify list - List classifications
* !users classify del [name] - Delete classification (must be owner)
* !users roomstats - List how many users are in each class in this room
* !users stats - List how many users are in each class globally as seen by bot

Example:

* !users classify add matrix.org @*:matrix.org
* !users classify add libera.chat @*:libera.chat
* !users classify add discord @*discordpuppet*:*
* !users stats
* !users roomstats

### RASP (Gliding Weather forecast)

Currently only Finnish RASP supported. Uses data from http://ennuste.ilmailuliitto.fi/

#### Usage

* !rasp [day] [hour]     - Fetch RASP for specified day and hour

Day and hour can be omitted - fetches today's forecast if not set.
PR welcome for supporting other data sources.

### Mumble

Show information about a configured mumble server,
including version, how many users are connected, and ping time.

#### Usage

* !mumble                                 - Show info about the configured mumble server
- !mumble (set|setserver) [host] ([port]) - Set the configured mumble server

## Bot setup

* Create a Matrix user
* Log in as the newly created user (easiest is Element Web in private window)
* Get user's access token (In Element Web see Settings / Help & about)

## Running locally

Run something like (tested on Ubuntu):

``` bash
sudo apt install python3-pip libcups2-dev libatlas-base-dev gcc
sudo pip3 install pipenv
pipenv shell
pipenv install --pre                       (this takes ages, go make a sandwich)
MATRIX_USER="@user:matrix.org" MATRIX_ACCESS_TOKEN="MDAxOGxvYlotofcharacters53CgYAYFgo" MATRIX_SERVER="https://matrix.org" JOIN_ON_INVITE=True BOT_OWNERS=@botowner:matrix.org
 python3 bot.py
```

NOTE: The Pipfile does not define the python version as it is always strict and causes problems. See https://github.com/pypa/pipenv/issues/1050 . Python 3.7 and 3.8 should both work fine.

## Running locally with systemd unit file (Raspberry Pi etc)

First modify run.sh and make sure Hemppa starts successfully with it.

There's a systemd unit file you can use. It assumes hemppa is installed to /opt/hemppa and
is run as user pi in group pi. Note: this is probably not the smartest way to do this, feel free
to do a PR for better way.

If your user is not pi, modify hemppa.service first.

``` bash
sudo ln -s `pwd` /opt/hemppa
sudo ln -s `pwd`/hemppa.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable hemppa.service
sudo systemctl start hemppa.service
sudo systemctl status hemppa.service
```

Status should show "Active: active (running)"

## Running with Docker

Create .env file and set variables:

``` bash
MATRIX_USER=@user:matrix.org
MATRIX_ACCESS_TOKEN=MDAxOGxvYlotofcharacters53CgYAYFgo
MATRIX_SERVER=https://matrix.org
JOIN_ON_INVITE=True
BOT_OWNERS=@user1:matrix.org,@user2:matrix.org
DEBUG=False
TZ=America/New_York
```

Note: without quotes!

Just run:

``` bash
docker-compose up
```

## Env variables

`MATRIX_USER` is the full MXID (not just username) of the Matrix user. `MATRIX_ACCESS_TOKEN`
and `MATRIX_SERVER` should be url to the user's server (non-delegated server). Set `JOIN_ON_INVITE` (default true) 
to false if you don't want the bot automatically joining rooms.

You can get access token by logging in with Element Android and looking from Settings / Help & About.

`BOT_OWNERS` is a comma-separated list of matrix id's for the owners of the bot.
Some commands require sender to be bot owner.
Typically set your own id into it.

`OWNERS_ONLY` is an optional variable once defined only the owners can operate the bot (this is a form of whitelisting)

`INVITE_WHITELIST` (default empty) is an optional comma-separated list of matrix id's to restrict the acceptance of invites into rooms of the bot to users or servers. It supports wild cards: Example value: `@user:matrix.org,@*:myserver.org`

`LEAVE_EMPTY_ROOMS` (default true) if this is set to false, the bot will stay in empty rooms

__*ATTENTION:*__ Don't include bot itself in `BOT_OWNERS` if cron or any other module that can cause bot to send custom commands is used, as it could potentially be used to run owner commands as the bot itself.

To enable debugging for the root logger set `DEBUG=True`.

`TZ` takes any valid [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) value and sets the bot server to the appropriate zone.

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
        await bot.send_text(room, ' '.join(args), event=None)

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

## Bot API
```python
class Bot:
    async def send_msg(self, mxid, roomname, message):
        """

        :param mxid: A Matrix user id to send the message to
        :param roomname: A Matrix room id to send the message to
        :param message: Text to be sent as message
        :return bool: Success upon sending the message
        """

    async def send_text(self, room, body, event=None, msgtype="m.notice", bot_ignore=False):
        """

        :param room: A MatrixRoom the text should be send to
        :param body: Textual content of the message
        :param event: The event to reply to
        :param msgtype: The message type for the room https://matrix.org/docs/spec/client_server/latest#m-room-message-msgtypes
        :param bot_ignore: Flag to mark the message to be ignored by the bot
        :return:
        """

    async def send_html(self, room, html, plaintext, event=None, msgtype="m.notice", bot_ignore=False):
        """

        :param room: A MatrixRoom the html should be send to
        :param html: Html content of the message
        :param plaintext: Plaintext content of the message
        :param event: The event to reply to
        :param msgtype: The message type for the room https://matrix.org/docs/spec/client_server/latest#m-room-message-msgtypes
        :param bot_ignore: Flag to mark the message to be ignored by the bot
        :return:
        """
        
    async def send_image(self, room, url, body, event=None, mimetype=None, width=None, height=None, size=None):
        """

        :param room: A MatrixRoom the image should be send to
        :param url: A MXC-Uri https://matrix.org/docs/spec/client_server/r0.6.0#mxc-uri
        :param body: A textual representation of the image
        :param event: The event to reply to
        :param mimetype: The mimetype of the image
        :param width: Width in pixel of the image
        :param height: Height in pixel of the image
        :param size: Size in bytes of the image
        :return:
        """
    
    async def upload_image(self, url, blob=False, blob_content_type="image/png"):
        """

        :param url: Url of binary content of the image to upload
        :param blob: Flag to indicate if the first param is an url or a binary content 
        :param blob_content_type: Content type of the image in case of binary content
        :return: A MXC-Uri https://matrix.org/docs/spec/client_server/r0.6.0#mxc-uri, Content type, Width, Height, Image size in bytes
        """
    
        
    async def upload_and_send_image(self, room, url, event=None, text=None, blob=False, blob_content_type="image/png"):
        """

        :param room: A MatrixRoom the image should be send to after uploading
        :param url: Url of binary content of the image to upload
        :param event: The event to reply to
        :param text: A textual representation of the image
        :param blob: Flag to indicate if the second param is an url or a binary content 
        :param blob_content_type: Content type of the image in case of binary content
        :return:
        """
    async def send_location(self, room, body, latitude, longitude, event=None bot_ignore=False):
        """

        :param room: A MatrixRoom the html should be send to
        :param html: Html content of the message
        :param body: Plaintext content of the message
        :param latitude: Latitude in WGS84 coordinates (float)
        :param longitude: Longitude in WGS84 coordinates (float)
        :param event: The event to reply to
        :param bot_ignore: Flag to mark the message to be ignored by the bot
        :return:
        """
```

### Logging

Uses [python logging facility](https://docs.python.org/3/library/logging.html) to print information to the console. Customize it to your needs editing `config/logging.yml`.
See [logging.config documentation](https://docs.python.org/3/library/logging.config.html) for further information.

Use `self.logger` in your module to print information to the console.

Module settings are stored in Matrix account data.

### Ignoring text messages

If you want to send a m.text message that bot should always ignore, set "org.vranki.hemppa.ignore" property in the event. Bot will ignore events with this set.
Set the bot_ignore parameter to True in sender functions to acheive this.

If you write a module that installs a custom message handler, use bot.should_ignore_event(event) to check if event should be ignored.

### Aliasing modules

A module can declare its own _aliases_ with the `add_module_aliases` command.
You probably want to call it during `matrix_start`:

```python
class MatrixModule(BotModule):

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, ['newname', 'anothername'])
```

Then you can call this module with its original name, `!newname`, or `!another-name`.
(Like module names, Hemppa ignores non-alphanumeric characters in aliases.)

## Contributing

If you write a new module, please make a PR if it's something useful for others.
