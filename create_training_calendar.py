#!python

from training_calendar import training_calendar
import sys

if __name__ == '__main__':
    try:
        args = sys.argv[1:]
        training_calendar.main(args)
    except training_calendar.TrainingCalendarError as e:
        print('error: {}'.format(e.message), file=sys.stderr)
        sys.exit(1)
