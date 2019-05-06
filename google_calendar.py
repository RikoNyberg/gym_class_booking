from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']


# class MemoryCache(Cache):
#     # This is a Class that is fixing a known cache bug: 
#     # https://stackoverflow.com/questions/40154672/importerror-file-cache-is-unavailable-when-using-python-client-for-google-ser
#     # https://github.com/googleapis/google-api-python-client/issues/325#issuecomment-274349841
#     
#     _CACHE = {}
#     def get(self, url):
#         return MemoryCache._CACHE.get(url)

#     def set(self, url, content):
#         MemoryCache._CACHE[url] = content

class GoogleCal():
    def __init__(self):
        self.service = self.get_service()

    def get_service(self):
        creds = None

        if os.path.exists('credentials/token.pickle'):
            with open('credentials/token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            with open('credentials/token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        if not creds:
            raise ValueError('Google API token.pickle is missing')
        service = build('calendar', 'v3', credentials=creds, cache_discovery=False)

        return service

    def list_events(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'], event['id'])

        if len(events):
            return events[0]['id']
        return None

    def add_event(self, class_name, start_time, end_time, email=None, accepted_attendee=False):
        if email:
            if accepted_attendee:
                attendee = [{'email': email, 'responseStatus': 'accepted'}]
            else:
                attendee = [{'email': email}]
        else:
            attendee = []

        event = {
            'summary': 'F24 - {}'.format(class_name),
            'location': 'Antinkatu 1, 00100 Helsinki',
            'description': 'Great job! Doing sports is always a good and healthy way to spend time :)',
            'start': {
                'dateTime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'Europe/Helsinki',
            },
            'end': {
                'dateTime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'Europe/Helsinki',
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=1'
            ],
            'attendees': attendee,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    # {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }
        event = self.service.events().insert(calendarId='primary', body=event).execute()

        return event['id']

    def remove_event(self, eventId):
        self.service.events().delete(calendarId='primary', eventId=eventId).execute()
        print('event removed:', eventId)

    def add_attendee(self, eventId, email, accepted_attendee=False):
        if accepted_attendee:
            attendee = {'email': email, 'responseStatus': 'accepted'}
        else:
            attendee = {'email': email}
        # First retrieve the event from the API.
        event = self.service.events().get(calendarId='primary', eventId=eventId).execute()
        event['attendees'].append(attendee)
        updated_event = self.service.events().update(
            calendarId='primary', eventId=event['id'], body=event).execute()

    def remove_attendee(self, eventId, email):
        # First retrieve the event from the API.
        event = self.service.events().get(calendarId='primary', eventId=eventId).execute()
        new_attendees = []
        for attendee in event['attendees']:
            if attendee['email'] == email:
                pass
            else:
                new_attendees.append(attendee)
        event['attendees'] = new_attendees
        self.service.events().update(calendarId='primary',
                                     eventId=event['id'], body=event).execute()

# cal = GoogleCal()
# eventId = cal.list_events()
# email = 'riko.nyberg@gmail.com'
# cal.add_accepted_attendee(eventId, email)
# cal.add_event()
# if eventId:
#     cal.remove_event(eventId)
