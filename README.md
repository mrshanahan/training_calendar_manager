# training\_calendar\_manager
---

Small set of scripts/tools for managing training calendars through the Google Calendar API.

#### Setup

If you are on a system that supports PowerShell, run the `setup.ps1` script to setup yourself up. There will be a manual step to download credentials:

    > .\setup.ps1

Otherwise, follow these steps:

1. Download and install [virtualenv].
1. `cd` into the cloned repository directory:

    > cd training_calendar_manager

1. Create a `virtualenv` in the given directory:

    > virtualenv .

1. Activate the virtualenv:

    > .\Scripts\activate

1. Install dependencies:

    > pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

1. Open a Chrome window pointing at the following URL, and click the button in step 1. It will ask you to download a credentials file; download it to the repository directory with the file name `credentials.json`:

    https://developers.google.com/google-apps/calendar/quickstart/python

Now you're ready to go!

#### Usage

To see the usage of the script + examples, run the Python executable with the script as an argument:

    > python create_training_calendar.py

If you find that you are having trouble authenticating, make sure that any existing `token.pickle` files in your current directory are deleted, then run the authentication again.

#### Direct Dependencies

- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`

#### Contents

- `create_training_calendar.py`
    - Creates a new training calendar from a template. Run the script without arguments to see usage.
