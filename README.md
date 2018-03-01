# training_calendar_manager
---

Small set of scripts/tools for managing training calendars through the Google Calendar API.

#### Setup

- (optional) Setup [virtualenv](https://virtualenv.pypa.io/en/stable/).
- Follow Step 1 of the [Google Calendar API Python QuickStart guide](https://developers.google.com/google-apps/calendar/quickstart/python). This will get you set up with a Google Developer account (if necessary) and save the necessary OAuth2 client credentials in the write place (`client_secret.json`, in the root of this repository.)
- You're ready to go!

#### Direct Dependencies

- `google-api-python-client`

#### Contents

- `create_training_calendar.py`
    - Creates a new training calendar from a template. Run the script without arguments to see usage.
