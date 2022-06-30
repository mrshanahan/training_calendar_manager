####################################
#          Google's Code           #
####################################

from __future__ import print_function
import os

import datetime
import pickle
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import datetime
import itertools
import sys
import csv

SCRIPT_NAME = "create_training_calendar.py"
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

EVENT_PROPERTIES_TO_RETAIN = ['summary','description','notes']
RACE_DAY_SUMMARY = 'RACE DAY'
TRAINING_CALENDAR_EVENT_DATE_FORMAT = '%Y-%m-%d'
TEMPLATE_CALENDAR_NAME = 'Iron Man 70.3 Training Template'

def get_calendar_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

####################################
#              My Code             #
####################################

class TrainingCalendarError(Exception):
    def __init__(self, message):
        self.message = message

class EventLoadError(TrainingCalendarError):
    pass

class Event:
    def __init__(self, start, end, properties):
        self.start = start
        self.end = end
        self.properties = { k: v for (k,v) in properties.items() if k in EVENT_PROPERTIES_TO_RETAIN }

    def build(self):
        event = dict(self.properties)
        event['start'] = { 'date': self.start.date().isoformat() }
        event['end'] = { 'date': self.end.date().isoformat() }
        return event

    def __str__(self):
        return "Event(start:{}, end:{}, {})".format(
                datetime.datetime.strftime(self.start, TRAINING_CALENDAR_EVENT_DATE_FORMAT),
                datetime.datetime.strftime(self.end, TRAINING_CALENDAR_EVENT_DATE_FORMAT),
                ', '.join(["{}:'{}'".format(k, v) for (k,v) in self.properties.items()]))


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

def copy_events2(service, events, to_calendar_id, tag=None):
    for event in events:
        new_event_body = event.build()
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

def load_events_from_calendar(service, calendar_name, race_day, ends_on_race_day):
    cal_id_map = get_calendar_name_id_map(service)
    if calendar_name not in cal_id_map:
        raise ValueError("Provided template calendar '{}' does not exist.".format(template_calendar_name))

    calendar_id = cal_id_map[template_calendar_name]
    cal_events = get_events_for_calendar(service, calendar_id=template_calendar_id, num_events=500)

    if ends_on_race_day:
        race_day_index = len(cal_events)-1
    else:
        race_day_index = find_race_day(cal_events)
    race_date = datetime.datetime.strptime(race_day, TRAINING_CALENDAR_EVENT_DATE_FORMAT)
    template_race_date = datetime.datetime.strptime(cal_events[race_day_index]['start']['date'], TRAINING_CALENDAR_EVENT_DATE_FORMAT)
    shift_dates_by = race_date - template_race_date

    events = [
        Event(
            start=datetime.datetime.strptime(e['start']['date'], TRAINING_CALENDAR_EVENT_DATE_FORMAT) + shift_dates_by,
            end=datetime.datetime.strptime(e['end']['date'], TRAINING_CALENDAR_EVENT_DATE_FORMAT) + shift_dates_by,
            properties={ k: v for (k,v) in e.items() if k not in ('start','end') })
        for e in cal_events]
    return events

def load_events_from_file(path, column_map, race_day, ends_on_race_day):
    events_raw = []
    race_day_index = -1
    column_map_lower = { k.lower(): v.lower() for (k,v) in column_map.items() }
    # TODO: Close file ASAP after opening
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for i,row in enumerate(reader):
            # TODO: Do this all at once, not per record.
            # TODO: Filter for EVENT_PROPERTIES_TO_RETAIN after column remap
            from_lower = { k.lower(): v for (k,v) in row.items() }
            to_lower = {}
            for from_c,to_c in column_map_lower.items():
                if to_c in to_lower:
                    exit_with_error(\
                        "cannot map column '{0}' to '{1}' because '{1}' is already mapped (file: {2})".format(\
                        from_c, to_c, path))
                elif from_c in from_lower and to_c in from_lower and to_c not in column_map_lower:
                    exit_with_error(\
                        "cannot map column '{0}' to '{1}' because '{1}' already exists and is not remapped (file: {2})".format(\
                        from_c, to_c, path))
                elif from_c in from_lower:
                    to_lower[to_c] = from_lower[from_c]
            for k in from_lower:
                if k not in column_map_lower:
                    to_lower[k] = from_lower[k]
            if 'summary' not in to_lower:
                exit_with_error("expected column 'summary', but none found (file: {})".format(path))
            events_raw.append(to_lower)

    if ends_on_race_day:
        race_day_index = len(events_raw)-1
    else:
        race_day_index = find_race_day(events_raw)

    if race_day_index < 0:
        exit_with_error(
            "no race day detected; ensure that there is a single event with the summary 'RACE DAY'" +
            " or pass the --ends-on-race-day switch to this script (file: {})".format(path))

    events = []
    race_day_dt = datetime.datetime.strptime(race_day, TRAINING_CALENDAR_EVENT_DATE_FORMAT)
    one_day = datetime.timedelta(days=1)
    for i,e in enumerate(events_raw):
        days = race_day_index - i
        this_dt = race_day_dt - datetime.timedelta(days=days)
        event = Event(start=this_dt, end=this_dt+one_day, properties=e)
        events.append(event)
    return events

def find_race_day(events):
    race_day_index = -1
    for i,e in enumerate(events):
        if e['summary'] == 'RACE DAY':
            if race_day_index >= 0:
                exit_with_error(\
                    "multiple events_raw with summary 'RACE DAY' found; expected at most 1 " +
                    "(second found in entry {})".format(i+1))
            race_day_index = i
    return race_day_index

def exit_with_error(msg):
    raise TrainingCalendarError(msg)
    print(msg, file=sys.stderr)
    sys.exit(1)

def help_and_exit():
    helpstr = """{script_upper}
    Create a training calendar in Google Calendars using a standard template or a
    CSV file of events.

USAGE:
    $ python {script} [-n] <new-calendar-name> [-r] <race-day> [options]

    -n,--name <name>                    Display name for the calendar to be created.
    -r,--race-day <date>                Date that the given race will take place. Format: '{fmt}'
    -f,--file <path>                    CSV file from which events should be copied.
    -c,--template-calendar <name>       Name of template calendar from which events should
                                          be copied.
    -t,--tag <name>                     Name of the tag with which each event in the calendar
                                          will be tagged.
    -m,--column-map <col>:<prop>[,...]  Provides a mapping of CSV columns to event properties.
                                          A warning will be written if this is used with -c,
                                          but it otherwise does nothing.
    --ends-on-race-day                  Indicates that the last event in the CSV file should be
                                          used as the race day. A warning will be written if this
                                          is used with -c, but it otherwise does nothing.
    --what-if                           Indicates that no calendars should be created or events
                                          copied, but the potential actions taken should be logged.
    -h,--help,-?                        Show this message & exit.

DESCRIPTION:
    The calendar will be set up such that the appropriate day in the training cycle
    lands on the given race day, generally the 16th Sunday in the cycle. The new calendar
    is aligned with the race day with the following decision:
        - If copying from a template calendar, then an event with the summary 'RACE DAY'
          is found, and each event in the template calendar is copied to the new
          calendar with its date shifted by the shift in the discovered race day.
        - If creating a new calendar from a CSV file, then an event with the summary
          'RACE DAY' is discovered in the CSV file and then the same process occurs.

CSV FILE FORMAT:
  - The CSV file must have columns 'Summary' and 'Description' (not case sensitive). These
    columns may be mapped using the -m/--column-map parameter, but an error will be thrown
    if they cannot be found.
  - Events will be added in-order; any day-of-week or date columns will be ignored.
  - Days must include weekends.
  - A 'Notes' column will also be recognized & used if available, mapping to the corresponding
    Google Calendar event property.
  - If a race day is not detected via the 'RACE DAY' summary & the --ends-on-race-day flag is
    not provided, an error will be thrown.

EXAMPLES:
  - Create a new calendar called 'Iron Dragon 2019' for a race day on June 15, 2019:

      $ python {script} \\
              -n 'Iron Dragon 2019' -r '2019-06-15' -c 'Iron Man 70.3 Training Template'

  - Create a new calendar called 'Iron Man 70.3 (Madison 2020)' for a race day on
    July 4, 2020 and tag each event with 'IM2020':

      $ python {script} \\
              -n 'Iron Man 70.3 (Madison 2020)' -r '2020-07-04' \\
              -c 'Iron Man 70.3 Training Template' -t 'IM2020'

  - Create a new calendar called 'Baltimore Marathon 2022' for a race day on
    October 15, 2022 using events from a CSV file called 'marathon_training.csv':

      $ cat marathon_training.csv | head -5
      Week,Day,Description,Notes
      1,Mon,15 min jog,"Allowed to walk, but not part of training"
      ,Tue,REST,
      ,Wed,20 min jog,"Allowed to walk, but not part of training"
      ,Thu,REST,
      $ python {script} \\
              -n 'Baltimore Marathon 2022' -r '2022-10-15' -f marathon_training.csv

""".format(script_upper=SCRIPT_NAME.upper(), script=SCRIPT_NAME, fmt=TRAINING_CALENDAR_EVENT_DATE_FORMAT)

    print(helpstr, file=sys.stderr)
    sys.exit(0)

def parse_arguments(args):
    inputs = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-n','--name'):
            if 'name' in inputs:
                msg = "--name already specified"
                exit_with_error(msg)
            inputs['name'] = args[i+1]
            i += 2
        elif arg in ('-r','--race-day'):
            if 'race_day' in inputs:
                msg = "--race-day already specified"
                exit_with_error(msg)
            inputs['race_day'] = args[i+1]
            i += 2
        elif arg in ('-f','--file'):
            if 'template_calendar_name' in inputs:
                exit_with_error('exactly one of --file or --template-calendar-name required (got both)')
            inputs['file'] = args[i+1]
            i += 2
        elif arg in ('-c','--template-calendar-name'):
            if 'file' in inputs:
                exit_with_error('exactly one of --file or --template-calendar-name required (got both)')
            inputs['template_calendar_name'] = args[i+1]
            i += 2
        elif arg in ('-t','--tag'):
            inputs['tag'] = args[i+1]
            i += 2
        elif arg in ('-m','--column-map'):
            inputs['column_map'] = args[i+1]
            i += 2
        elif arg == '--ends-on-race-day':
            inputs['ends_on_race_day'] = True
            i += 1
        elif arg == '--what-if':
            inputs['what_if'] = True
            i += 1
        elif arg in ('-h','--help','help','?','-?'):
            help_and_exit()
        else:
            if 'name' in inputs:
                if 'race_day' in inputs:
                    msg = 'invalid positional argument (--name & --race-day already specified): {}'.format(arg)
                    exit_with_error(msg)
                inputs['race_day'] = arg
            else:
                inputs['name'] = arg
            i += 1

    no_required_arg_fmt = 'missing required argument: {}'
    if 'name' not in inputs:
        msg = no_required_arg_fmt.format('--name')
        exit_with_error(msg)
    if 'race_day' not in inputs:
        msg = no_required_arg_fmt.format('--race-day')
        exit_with_error(msg)
    if 'file' not in inputs and 'template_calendar_name' not in inputs:
        exit_with_error('exactly one of --file or --template-calendar-name required (got neither)')

    return inputs

# TODO: Test me
def parse_column_map(column_map):
    pairs = column_map.split(',')
    mapped = [tuple(p.split(':')) for p in pairs]
    return dict(mapped)

def main(args):
    inputs = parse_arguments(args)

    new_calendar_name = inputs['name']
    race_day = inputs['race_day']
    if 'tag' in inputs:
        tag = inputs['tag']
    else:
        tag = None

    service = get_calendar_service()
    if 'file' in inputs:
        column_map = parse_column_map(inputs['column_map']) if 'column_map' in inputs else {}
        events = load_events_from_file(inputs['file'], column_map, race_day, inputs.get('ends_on_race_day', False))
        shift_dates_by = datetime.timedelta(days=0)
    elif 'template_calendar_name' in inputs:
        events = load_events_from_calendar(service, inputs['template_calendar_name'])
        if inputs['ends_on_race_day']:
            race_day_index = len(events)-1
        else:
            race_day_index = find_race_day(events)
        race_date = datetime.datetime.strptime(race_day, TRAINING_CALENDAR_EVENT_DATE_FORMAT)
        shift_dates_by = race_date - events[race_day_index].date 
    else:
        exit_with_error('exactly one of --file or --template-calendar-name required (got neither)')

    cal_id_map = get_calendar_name_id_map(service)
    if new_calendar_name not in cal_id_map:
        print("{}Creating new calendar".format('WHAT-IF: ' if inputs.get('what_if', False) else ''))
        if not inputs.get('what_if', False):
            new_calendar_data = { 'summary': new_calendar_name, 'timeZone': 'America/Chicago', 'accessRole': 'owner' }
            new_calendar_result = service.calendars().insert(body=new_calendar_data).execute()
            print("New calendar created: {}".format(new_calendar_result))
            new_calendar_id = new_calendar_result['id']
    else:
        new_calendar_id = cal_id_map[new_calendar_name]
        print("Calendar '{}' (id='{}') already exists".format(new_calendar_name, new_calendar_id))

    if inputs.get('what_if', False):
        for e in events:
            print("WHAT-IF: Copying event: {} (tag: {})".format(str(e), tag if tag else '<NONE>'))
    else:
        copy_events2(service, events, new_calendar_id, tag)
        #create_training_calendar(service, new_calendar_name, TEMPLATE_CALENDAR_NAME, race_day, tag=tag)

if __name__ == '__main__':
    try:
        args = sys.argv[1:]
        main(args)
    except TrainingCalendarError as e:
        print('error: {}'.format(e.message), file=sys.stderr)
        sys.exit(1)
