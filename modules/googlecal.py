from __future__ import print_function
from datetime import datetime
import datetime
import pickle
import os.path
import time
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request



#
# Google calendar notifications
#
# Note: Provide a token.pickle file for the service. 
# It's created on first run (run from console!) and 
# can be copied to another computer.
#
# ENV variables:
#
# Google calendar creds file: (defaults to this)
# GCAL_CREDENTIALS="credentials.json"
#

class MatrixModule:
    def matrix_start(self, bot):
        self.bot = bot
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.credentials_file = "credentials.json"
        if os.getenv("GCAL_CREDENTIALS"):
            self.credentials_file = os.getenv("GCAL_CREDENTIALS")
        self.service = None
        self.calendar_rooms = dict() # Contains room_id -> [calid, calid] ..

        creds = None

        if not os.path.exists(self.credentials_file):
            return # No-op if not set up

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

        calendar_list = self.service.calendarList().list().execute()['items']

        print(f'Google calendar set up successfully with access to {len(calendar_list)} calendars:\n')
        for calendar in calendar_list:
            print(calendar['summary'] + ' - ' + calendar['id'])


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
                    print('Listing events in cal', calid)
                    events = events + self.list_today(calid)
            if args[1] == 'calendars':
                await bot.send_text(room, 'Calendars in this room: ' + str(self.calendar_rooms.get(room.room_id)))
        elif len(args) == 3:
            if args[1] == 'add':
                calid = args[2]
                print(f'Adding calendar {calid} to room id {room.room_id}')

                if self.calendar_rooms.get(room.room_id):
                    if calid not in self.calendar_rooms[room.room_id]:
                        self.calendar_rooms[room.room_id].append(calid)
                    else:
                        await bot.send_text(room, 'This google calendar already added in this room!')
                        return
                else:
                    self.calendar_rooms[room.room_id] = [calid]

                print(f'Calendars now for this room {self.calendar_rooms.get(room.room_id)}')

                bot.save_settings()

                await bot.send_text(room, 'Added new google calendar to this room')
            if args[1] == 'del':
                calid = args[2]
                print(f'Removing calendar {calid} from room id {room.room_id}')

                if self.calendar_rooms.get(room.room_id):
                    self.calendar_rooms[room.room_id].remove(calid)

                print(f'Calendars now for this room {self.calendar_rooms.get(room.room_id)}')

                bot.save_settings()

                await bot.send_text(room, 'Removed google calendar from this room')
        else:
            for calid in calendars:
                print('Listing events in cal', calid)
                events = events + self.list_upcoming(calid)

            if len(events) == 0:
                await bot.send_text(room, 'No events found.')
            else:
                print(f'Found {len(events)} events')
                await self.send_events(bot, events, room)

    async def send_events(self, bot, events, room):
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # await bot.send_text(room, f"{self.parse_date(start)} {event['summary']}")
            # await bot.send_text(room, f"{self.parse_date(start)} {event['summary']} {event['htmlLink']}")
            await bot.send_html(room, f'{self.parse_date(start)} <a href="{event["htmlLink"]}">{event["summary"]}</a>', f'{self.parse_date(start)} {event["summary"]}')

    def list_upcoming(self, calid):
        startTime = datetime.datetime.utcnow()
        now = startTime.isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calid, timeMin=now,
                                            maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        return events

    def list_today(self, calid):
        startTime = datetime.datetime.utcnow()
        startTime = startTime - datetime.timedelta(hours=startTime.hour, minutes=startTime.minute)
        endTime = startTime + datetime.timedelta(hours=24)
        now = startTime.isoformat() + 'Z'
        end = endTime.isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calid, timeMin=now,
                                                    timeMax=end, maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        return events

    def help(self):
        return('Google calendar. Lists 10 next events by default. today = list today\'s events.')

    def get_settings(self):
        return { 'calendar_rooms': self.calendar_rooms }

    def set_settings(self, data):
        if data.get('calendar_rooms'):
            self.calendar_rooms = data['calendar_rooms']

    def parse_date(self, start):
        try: 
            dt = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
            return dt.strftime("%d.%m %H:%M")
        except ValueError:
            dt = datetime.datetime.strptime(start, '%Y-%m-%d')
            return dt.strftime("%d.%m")
