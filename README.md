# Hemppa - generic modular Matrix bot

This bot is meant to be super easy platform to code Matrix bot functionality
with Python. It uses matrix-nio library https://github.com/poljar/matrix-nio/ .

Type !help in room with this bot running to list active modules.

## Module list

### Help

Prints help on existing modules.

### Echo

Simple example module that just echoes what user said.

### Metar

Aviation weather metar service access.

### TAF 

Aviation weather TAF service access.

### Uptime

Prints bot uptime.

### Google Calendar (WIP)

Displays changes and daily report of a google calendar to a room. This is a bit pain to set up, sorry.

To set up, you'll need to generate credentials.json file - see https://console.developers.google.com/apis/credentials

When credentials.json is present, you must authenticate the bot to access calendar. There will be a link in console like this:

``` text
Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=907....
```

Open the link and authenticate as needed. A new file token.pickle will be created in the directory and bot will read it in future. 

Now the bot should be usable.

Use !googlecal add [calendar id] to add new calendar to a room. The bot lists availble calendar ID's on startup and you can find them
in google calendar.

Commands:

* !googlecal - Show next 10 events in calendar
* !googlecal today - Show today's events
* !googlecal add [calendar id] - Add new calendar to room
* !googlecal calendars - List calendars in this room

## Bot setup

* Create a Matrix user
* Get user's access token - In Riot Web see Settings / Help & about

## Running on host

Run something like:

``` bash
pip3 install pipenv
pipenv shell
pipenv install
MATRIX_USER="@user:matrix.org" MATRIX_ACCESS_TOKEN="MDAxOGxvYlotofcharacters53CgYAYFgo" MATRIX_SERVER="https://matrix.org" JOIN_ON_INVITE=True python3 bot.py
```

## Running with Docker

Create .env file and set variables:

``` bash
MATRIX_USER=@user:matrix.org
MATRIX_ACCESS_TOKEN=MDAxOGxvYlotofcharacters53CgYAYFgo
MATRIX_SERVER=https://matrix.org
JOIN_ON_INVITE=True
```

Note: without quotes!

Just run:

``` bash
docker-compose up
```

## Env variables

User, access token and server should be self-explanatory. Set JOIN_ON_INVITE to anything if you want the bot to
join invites automatically.

You can set MATRIX_PASSWORD if you want to get access token. Normally you can use Riot to get it.

## Module API

Just write a python file with desired command name and place it in modules. See current modules for
examples. No need to register it anywhere else.

Functions:

* matrix_start - Called once on startup
* async matrix_message - Called when a message is sent to room starting with !module_name
* matrix_stop - Called once before exit
* async matrix_poll - Called every 10 seconds
* help - Return one-liner help text

You only need to implement the ones you need. See existing bots for examples
