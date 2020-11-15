from __future__ import print_function

import os
import os.path
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

#
# Google calendar notifications
#
# Note: Provide a token.pickle file for the service.
# It's created on first run (run from console!) and
# can be copied to another computer.
#
from modules.common.module import BotModule


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.credentials_file = "credentials.json"
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.bot = None
        self.service = None
        self.calendar_rooms = dict()  # Contains room_id -> [calid, calid] ..
        self.enabled = False

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot
        creds = None

        if not os.path.exists(self.credentials_file) or os.path.getsize(self.credentials_file) == 0:
            return  # No-op if not set up

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                self.logger.info('Loaded existing pickle file')
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            self.logger.warn('No credentials or credentials not valid!')
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                # urn:ietf:wg:oauth:2.0:oob
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                self.logger.info('Pickle saved')

        self.service = build('calendar', 'v3', credentials=creds)

        try:
            calendar_list = self.service.calendarList().list().execute()['items']
            self.logger.info(f'Google calendar set up successfully with access to {len(calendar_list)} calendars:\n')
            for calendar in calendar_list:
                self.logger.info(f"{calendar['summary']} - + {calendar['id']}")
        except Exception:
            self.logger.error('Getting calendar list failed!')

    async def matrix_message(self, bot, room, event):
        if not self.service:
            await bot.send_text(room, 'Google calendar not set up for this bot.')
            return
        args = event.body.split()
        events = []
        calendars = self.calendar_rooms.get(room.room_id) or []

        if len(args) == 2:
            if args[1] == 'today':
                for calid in calendars:
                    self.logger.info(f'Listing events in cal {calid}')
                    events = events + self.list_today(calid)
            if args[1] == 'list':
                await bot.send_text(room, 'Calendars in this room: ' + str(self.calendar_rooms.get(room.room_id)))
                return

        elif len(args) == 3:
            if args[1] == 'add':
                bot.must_be_admin(room, event)

                calid = args[2]
                self.logger.info(f'Adding calendar {calid} to room id {room.room_id}')

                if self.calendar_rooms.get(room.room_id):
                    if calid not in self.calendar_rooms[room.room_id]:
                        self.calendar_rooms[room.room_id].append(calid)
                    else:
                        await bot.send_text(room, 'This google calendar already added in this room!')
                        return
                else:
                    self.calendar_rooms[room.room_id] = [calid]

                self.logger.info(f'Calendars now for this room {self.calendar_rooms.get(room.room_id)}')

                bot.save_settings()

                await bot.send_text(room, 'Added new google calendar to this room')
                return

            if args[1] == 'del':
                bot.must_be_admin(room, event)

                calid = args[2]
                self.logger.info(f'Removing calendar {calid} from room id {room.room_id}')

                if self.calendar_rooms.get(room.room_id):
                    self.calendar_rooms[room.room_id].remove(calid)

                self.logger.info(f'Calendars now for this room {self.calendar_rooms.get(room.room_id)}')

                bot.save_settings()

                await bot.send_text(room, 'Removed google calendar from this room')
                return

        else:
            for calid in calendars:
                self.logger.info(f'Listing events in cal {calid}')
                events = events + self.list_upcoming(calid)

        if len(events) > 0:
            self.logger.info(f'Found {len(events)} events')
            await self.send_events(bot, events, room)
        else:
            self.logger.info(f'No events found')
            await bot.send_text(room, 'No events found, try again later :)')

    async def send_events(self, bot, events, room):
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            await bot.send_html(room, f'{self.parse_date(start)} <a href="{event["htmlLink"]}">{event["summary"]}</a>',
                                f'{self.parse_date(start)} {event["summary"]}')

    def list_upcoming(self, calid):
        startTime = datetime.utcnow()
        now = startTime.isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calid, timeMin=now,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        return events

    def list_today(self, calid):
        startTime = datetime.utcnow()
        startTime = startTime.replace(hour=0, minute=0, second=0, microsecond=0)
        endTime = startTime + timedelta(hours=24)
        now = startTime.isoformat() + 'Z'
        end = endTime.isoformat() + 'Z'
        self.logger.info(f'Looking for events between {now} {end}')
        events_result = self.service.events().list(calendarId=calid, timeMin=now,
                                                   timeMax=end, maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        return events_result.get('items', [])

    def help(self):
        return 'Google calendar. Lists 10 next events by default. today = list today\'s events.'

    def get_settings(self):
        data = super().get_settings()
        data['calendar_rooms'] = self.calendar_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('calendar_rooms'):
            self.calendar_rooms = data['calendar_rooms']

    def parse_date(self, start):
        try:
            dt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
            return dt.strftime("%d.%m %H:%M")
        except ValueError:
            dt = datetime.strptime(start, '%Y-%m-%d')
            return dt.strftime("%d.%m")
