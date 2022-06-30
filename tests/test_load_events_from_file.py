from training_calendar import training_calendar as sut
from datetime import datetime, timedelta
from os import path
import io
import pytest

DATE_FORMAT = '%Y-%m-%d'

def get_test_file(name):
    return path.join(path.dirname(path.abspath(__file__)), name)

def test_golden():
    test_file = get_test_file('golden.csv')
    events = sut.load_events_from_file(test_file, {}, '2022-10-15', False)
    assert len(events) == 6
    race_date = datetime.strptime('2022-10-15', DATE_FORMAT)
    expected_race_date_index = 4
    for i,e in enumerate(events):
        expected_start = race_date + timedelta(days=(i-expected_race_date_index))
        expected_end = expected_start + timedelta(days=1)
        assert 'summary' in e.properties
        assert expected_start == e.start
        assert expected_end == e.end
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_no_race_day():
    test_file = get_test_file('no-race-day.csv')
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        events = sut.load_events_from_file(test_file, {}, '2022-10-15', False)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('no race day detected')

def test_no_race_day_and_ends_on_race_day():
    test_file = get_test_file('no-race-day.csv')
    race_date = datetime.strptime('2022-10-15', DATE_FORMAT)
    events = sut.load_events_from_file(test_file, {}, '2022-10-15', True)
    assert events[-1].start == race_date

def test_race_day_but_ends_on_race_day():
    test_file = get_test_file('golden.csv')
    race_date = datetime.strptime('2022-10-15', DATE_FORMAT)
    events = sut.load_events_from_file(test_file, {}, '2022-10-15', True)
    assert events[-1].start == race_date

def test_raises_on_no_summary_column():
    test_file = get_test_file('no-summary.csv')
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        events = sut.load_events_from_file(test_file, {}, '2022-10-15', False)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith("expected column 'summary', but none found")

def test_remaps_column_if_not_exists():
    test_file = get_test_file('no-summary.csv')
    events = sut.load_events_from_file(test_file, {'foobar': 'summary'}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert 'foobar' not in e.properties
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_remap_single_column_out_of_many():
    test_file = get_test_file('remap-existing-column.csv')
    events = sut.load_events_from_file(test_file, {'foobar': 'summary'}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert 'foobar' not in e.properties
        assert e.properties['description'] == 'Desc{}'.format(i)
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_remap_multiple_columns():
    test_file = get_test_file('remap-existing-column.csv')
    events = sut.load_events_from_file(test_file, {'foobar': 'summary', 'description': 'notes'}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert 'foobar' not in e.properties
        assert 'description' not in e.properties
        assert e.properties['notes'] == 'Desc{}'.format(i)
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_remap_ignores_unused_columns():
    test_file = get_test_file('remap-existing-column.csv')
    events = sut.load_events_from_file(test_file, {'foobar': 'summary', 'flimflam': 'description', 'coolio': 'radical', 'description': 'notes'}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert 'foobar' not in e.properties
        assert 'description' not in e.properties
        assert 'flimflam' not in e.properties
        assert 'coolio' not in e.properties
        assert 'radical' not in e.properties
        assert e.properties['notes'] == 'Desc{}'.format(i)
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_remap_drops_unretained_columns():
    test_file = get_test_file('remap-existing-column.csv')
    events = sut.load_events_from_file(test_file, {'foobar': 'summary', 'description': 'blech'}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert 'foobar' not in e.properties
        assert 'description' not in e.properties
        assert 'blech' not in e.properties
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)


# TODO: Parameterized so that we don't rely on dictionary order
def test_remaps_column_if_target_already_remapped():
    test_file = get_test_file('remap-existing-column.csv')
    events = sut.load_events_from_file(test_file, {'foobar': 'summary', 'description': 'foobar'}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert 'foobar' not in e.properties
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_raises_on_multiple_remap_to_same_column():
    test_file = get_test_file('remap-existing-column.csv')
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        events = sut.load_events_from_file(test_file, {'foobar': 'summary', 'description': 'summary'}, '2022-10-15', False)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith("cannot map column 'description' to 'summary' because 'summary' is already mapped")

def test_raises_on_remap_to_existing_column():
    test_file = get_test_file('remap-existing-column-3.csv')
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        events = sut.load_events_from_file(test_file, {'foobar': 'summary', 'description': 'flimflam'}, '2022-10-15', False)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith("cannot map column 'description' to 'flimflam' because 'flimflam' already exists and is not remapped")

def test_column_names_lowercase():
    test_file = get_test_file('column-names-variable-case.csv')
    events = sut.load_events_from_file(test_file, {}, '2022-10-15', False)
    for i,e in enumerate(events):
        assert e.properties['description'] == 'Desc{}'.format(i)
        assert e.properties['notes'] == 'Note{}'.format(i)
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)

def test_remap_is_coerced_to_lowercase():
    test_file = get_test_file('column-names-variable-case.csv')
    events = sut.load_events_from_file(test_file, {'desCRIPtion': 'NOTES', 'noTES': 'descriptioN' }, '2022-10-15', False)
    for i,e in enumerate(events):
        assert e.properties['description'] == 'Note{}'.format(i)
        assert e.properties['notes'] == 'Desc{}'.format(i)
        if i == 4:
            assert e.properties['summary'] == 'RACE DAY'
        else:
            assert e.properties['summary'] == 'Test{}'.format(i)
