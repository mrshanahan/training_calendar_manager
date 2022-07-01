# training\_calendar\_manager
---

Small set of scripts/tools for managing training calendars through the Google Calendar API.

#### Setup

Run the setup script via `source` from the root directory:

    $ source ./setup.sh

This will:
- Check that non-virtualenv dependencies are installed
- Create a virtualenv
- Activate the virtualenv
- Install Python dependencies

Then you have to get a credential:

1. Open a Chrome window pointing at the following URL, and click the button in step 1. It will ask you to download a credentials file; download it to the repository directory with the file name `credentials.json`:

    https://developers.google.com/google-apps/calendar/quickstart/python

Now you're ready to go!

#### Usage

The `create_training_calendar.py` script can be run as an executable or via `python`:

    $ ./create_training_calendar.py ...
    # OR
    $ python ./create_training_calendar.py ...

To see the usage of the script + examples, pass the `--help` flag:

    $ ./create_training_calendar.py --help

The application is implemeented in a module, so you can import the module & use it in the REPL:

    $ python
    ...
    > import training_calendar

If you find that you are having trouble authenticating, make sure that any existing `token.json` files in your current directory are deleted, then run the authentication again.

### Tests

Run tests using `pytest`:

    # Assumes you are in a virtualenv
    $ pip install pytest
    $ python -m pytest

`pytest` will pick up all test files under the current directory.

#### Direct Dependencies

- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`

#### Contents

- `training_calendar/`
    - Module for creating training calendars.
- `tests/`
    - Tests for the `training_calendar` module.
- `create_training_calendar.py`
    - Wrapper script to run the `training_calendar` module.
- `README.md`
    - This file.
- `setup.sh`
    - Script to perform initial setup before running `create_training_calendar.py`.

