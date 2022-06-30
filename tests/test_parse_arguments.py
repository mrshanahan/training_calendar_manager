from training_calendar import training_calendar as sut
from datetime import datetime, timedelta
from os import path
import io
import pytest
import random

def test_raises_when_empty():
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments([])
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('missing required argument: --name')

def test_raises_when_no_calendar_name():
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(['--race-day', '2022-10-15'])
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('missing required argument: --name')

@pytest.mark.parametrize('args', [
    ['Marathon'],
    ['Cool Marathon'],
    ['--name', 'Marathon'],
    ['-n', 'Marathon'],
])
def test_raises_when_no_race_day(args):
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(args)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('missing required argument: --race-day')

@pytest.mark.parametrize('args', [
    ['--name','Marathon','-n','Cool Thing'],
    ['-n','Marathon','--name','Cool Thing']
])
def test_raises_when_multiple_calendar_name(args):
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(args)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('--name already specified')

@pytest.mark.parametrize('args', [
    ['--name','Marathon','-r','2022-10-15','--race-day','2022-11-15'],
    ['Cool Thing','2022-10-15','-r','2023-10-15'],
    ['-r','2022-11-15','Marathon','--race-day','2022-10-15']
])
def test_raises_when_multiple_race_day(args):
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(args)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('--race-day already specified')

def test_raises_when_neither_file_nor_template_calendar():
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(['-n','Marathon','-r','2022-10-15'])
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('exactly one of --file or --template-calendar-name required (got neither)')

@pytest.mark.parametrize('args', [
    ['-n','Marathon','-r','2022-10-15','-f','./file.csv','-c','Source Calendar'],
    ['-n','Marathon','-r','2022-10-15','-c','Source Calendar','-f','./file.csv'],
    ['-n','Marathon','-r','2022-10-15','--file','./file.csv','--template-calendar-name','Source Calendar'],
])
def test_raises_when_both_file_and_template_calendar(args):
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(args)
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('exactly one of --file or --template-calendar-name required (got both)')

def test_raises_when_too_many_positional_args():
    with pytest.raises(sut.TrainingCalendarError) as exc_info:
        inputs = sut.parse_arguments(['Calendar','2022-10-15','FooBar'])
    assert exc_info.type is sut.TrainingCalendarError
    assert exc_info.value.message.startswith('invalid positional argument')

@pytest.mark.parametrize('expected_name,expected_race_day,args', [
    ('Marathon', '2022-10-15', ['-n','Marathon','-r','2022-10-15','-f','./file.csv']),
    ('Marathon', '2022-10-15', ['--name','Marathon','--race-day','2022-10-15','-f','./file.csv']),
    ('Marathon', '2022-10-15', ['-n','Marathon','-r','2022-10-15','-c','Source Calendar']),
    ('Marathon', '2022-10-15', ['--name','Marathon','--race-day','2022-10-15','-c','Source Calendar']),
    ('Marathon', '2022-10-15', ['Marathon','-r','2022-10-15','-c','Source Calendar']),
    ('Marathon', '2022-10-15', ['-r','2022-10-15','Marathon','-c','Source Calendar']),
    ('Marathon', '2022-10-15', ['Marathon','2022-10-15','--template-calendar-name','Source Calendar']),
])
def test_gets_reqd_args_from_position(expected_name, expected_race_day, args):
    inputs = sut.parse_arguments(args)
    assert inputs['name'] == expected_name
    assert inputs['race_day'] == expected_race_day

additional_args = {
    'tag': ('-t','--tag','TAG'),
    'column_map': ('-m','--column-map','foo=bar,bing=baz'),
    'ends_on_race_day': (None,'--ends-on-race-day',None),
    'what_if': (None,'--what-if',None),
}

def __choose_arg(arg):
    if arg[0] is not None:
        if random.random() < 0.5:
            return [arg[0], arg[2]]
        else:
            return [arg[1], arg[2]]
    else:
        return [arg[1]]

def __sample_args(additional_args):
    num_additional_args = random.randint(0, len(additional_args))
    sampled_args = random.sample(list(additional_args.items()), num_additional_args)
    random.shuffle(sampled_args)
    args = ['Marathon', '2022-10-15', '-f', './test.csv']
    arg_map = {}
    for (k,v) in sampled_args:
        arg_map[k] = v
        args.extend(__choose_arg(v))
    return args, arg_map

def test_other_args():
    for _ in range(50):
        args, arg_map = __sample_args(additional_args)
        inputs = sut.parse_arguments(args)
        for k,v in arg_map.items():
            assert k in inputs
            if v[2] == None:
                assert inputs[k] == True
            else:
                assert inputs[k] == v[2]
