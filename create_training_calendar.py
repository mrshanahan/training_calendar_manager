####################################
#          Google's Code           #
####################################

from __future__ import print_function
import os

import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import datetime
import itertools
import sys

SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

SCRIPT_NAME = os.path.basename(sys.argv[0])
EVENT_PROPERTIES_TO_RETAIN = ['summary','description','notes']
RACE_DAY_SUMMARY = 'RACE DAY'
TRAINING_CALENDAR_EVENT_DATE_FORMAT = '%Y-%m-%d'
TEMPLATE_CALENDAR_NAME = 'Iron Man 70.3 Training Template'

def get_calendar_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

####################################
#              My Code             #
####################################

# Debugging utility
def print_table(dicts, keys=[]):
    if not keys:
        keys = sorted(set(itertools.chain(*[d.keys() for d in dicts])))
    column_lens = { k: (max(len(k), *[len(str(d.get(k, ''))) for d in dicts]) + 1) for k in keys }
    format_str = ' '.join(["{{:<{}}}"] * len(keys)).format(*[column_lens[k] for k in keys])
    print(format_str.format(*keys))
    print(format_str.format(*['-'*column_lens[k] for k in keys]))
    for d in dicts:
        print(format_str.format(*[d.get(k,'') for k in keys]))

def get_events_for_calendar(service, calendar_id='primary', num_events=10, from_time=(datetime.datetime.min.isoformat() + 'Z')):
    eventsResult = service.events().list(
        calendarId=calendar_id, timeMin=from_time, maxResults=num_events, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events

def get_calendar_name_id_map(service):
    calendars = service.calendarList().list().execute().get('items', [])
    return {c['summary']: c['id'] for c in calendars}

def copy_events(service, events, to_calendar_id, shift_dates_by=datetime.timedelta(0), tag=None):
    for event in events:
        event_start_date = datetime.datetime.strptime(event['start']['date'], TRAINING_CALENDAR_EVENT_DATE_FORMAT)
        new_event_start_date = event_start_date + shift_dates_by
        new_event_end_date = event_start_date + datetime.timedelta(shift_dates_by.days+1)
        new_event_start = { 'date': new_event_start_date.date().isoformat() }
        new_event_end = { 'date': new_event_end_date.date().isoformat() }

        new_event_body = { k: event[k] for k in EVENT_PROPERTIES_TO_RETAIN if k in event }
        new_event_body['start'] = new_event_start
        new_event_body['end'] = new_event_end
        if tag:
            new_event_body['etag'] = tag

        print('Creating event: {}'.format(new_event_body))
        new_event_result = service.events().insert(calendarId=to_calendar_id, body=new_event_body).execute()

def create_training_calendar(service, new_calendar_name, template_calendar_name, race_day, tag=None):
    if type(race_day) is str:
        race_day = datetime.datetime.strptime(race_day, TRAINING_CALENDAR_EVENT_DATE_FORMAT)

    cal_id_map = get_calendar_name_id_map(service)
    if template_calendar_name not in cal_id_map:
        raise ValueError("Provided template calendar '{}' does not exist.".format(template_calendar_name))

    template_calendar_id = cal_id_map[template_calendar_name]
    template_events = get_events_for_calendar(service, calendar_id=template_calendar_id, num_events=500)
    potential_template_race_days = [e for e in template_events if e['summary'] == RACE_DAY_SUMMARY]
    if len(potential_template_race_days) == 0:
        raise ValueError(
            "No event found in template calendar ('{}') which matches string '{}'. " + 
            "Please make sure such an event exists and run again.".format(template_calendar_name, RACE_DAY_SUMMARY))
    if len(potential_template_race_days) > 1:
        raise ValueError(
            "Found {} events with summary '{}' in template calendar ('{}'). " + 
            "Ensure only one such event exists.".format(len(potential_template_race_days), RACE_DAY_SUMMARY, template_calendar_name))
    template_race_day = datetime.datetime.strptime(potential_template_race_days[0]['start']['date'], TRAINING_CALENDAR_EVENT_DATE_FORMAT)
    print('Race day: {}'.format(template_race_day))
    race_day_diff = race_day - template_race_day
    print('Race day diff: {}'.format(race_day_diff))

    if new_calendar_name not in cal_id_map:
        print("Creating new calendar")
        new_calendar_data = { 'summary': new_calendar_name, 'timeZone': 'America/Chicago', 'accessRole': 'owner' }
        new_calendar_result = service.calendars().insert(body=new_calendar_data).execute()
        print("New calendar created: {}".format(new_calendar_result))
        new_calendar_id = new_calendar_result['id']
    else:
        new_calendar_id = cal_id_map[new_calendar_name]
        print("Calendar '{}' (id='{}') already exists".format(new_calendar_name, new_calendar_id))

    copy_events(service, template_events, new_calendar_id, shift_dates_by=race_day_diff, tag=tag)

    print("Complete!")

def help():
    helpstr = """{script_upper}
    Create a triathlon training calendar in Google Calendars using a standard template.
    The calendar will be set up such that the appropriate day in the training cycle
    lands on the given race day (i.e. the 16th Sunday in the cycle).

USAGE:
    $ python {script} CALENDAR-NAME RACE-DAY [EVENT-TAG]

    CALENDAR-NAME
        Display name for the calendar to be created.
    RACE-DAY
        Date that the given race will take place. Format: '{fmt}'
    EVENT-TAG
        (optional) Name of the tag with which each event in the calendar will be tagged.

EXAMPLES:
  - Create a new calendar called 'Iron Dragon 2019' for a race day on June 15, 2019:

      $ python {script} 'Iron Dragon 2019' '2019-06-15'

  - Create a new calendar called 'Iron Man 70.3 (Madison 2020)' for a race day on
    July 4, 2020 and tag each event with 'IM2020':

      $ python {script} 'Iron Man 70.3 (Madison 2020)' '2020-07-04' 'IM2020'

""".format(script_upper=SCRIPT_NAME.upper(), script=SCRIPT_NAME, fmt=TRAINING_CALENDAR_EVENT_DATE_FORMAT)

    print(helpstr, file=sys.stderr)
    sys.exit(0)

def main():
    args = sys.argv[1:]
    if len(args) < 2:
        help()
    if len(args) > 3:
        print("{}: warning: expected at most 4 arguments, got {}; ignoring rest".format(sys.argv[0], len(args)), file=sys.stderr)
    new_calendar_name = args[0]
    race_day = args[1]
    if len(args) >= 4:
        tag = args[2]
    else:
        tag = None

    service = get_calendar_service()
    create_training_calendar(service, new_calendar_name, TEMPLATE_CALENDAR_NAME, race_day, tag=tag)

if __name__ == '__main__':
    main()
