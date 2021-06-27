import os
import sys
import threading
import traceback
from datetime import datetime, timedelta, time
from logging import Logger
from pathlib import Path
from typing import Optional

from demo1.api.demo1_error import Demo1Error

ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def _short(filename: str) -> str:
    file_name_components = filename.split('/')
    if len(file_name_components) == 0:
        return ''
    return file_name_components[len(file_name_components) - 1]


def print_threads():
    """
    Custom print current threads and them stack-traces
    """
    all_threads = {}
    all_stack_traces = []

    for thread in threading.enumerate():
        all_threads[thread.ident] = thread.name

    for thread_id, stack in sys._current_frames().items():
        all_stack_traces.append('\n# ThreadID: %s, %s' % (thread_id, all_threads.get(thread_id)))
        for filename, line_no, name, line in traceback.extract_stack(stack):
            line_of_trace = '%s, line %d, in %s' % (_short(filename),
                                                    line_no, name)
            next_info_start = max(len(line_of_trace), 70)
            line_of_trace = line_of_trace.ljust(next_info_start) + ' %s' % (line.strip())
            all_stack_traces.append(line_of_trace)
    for line_of_trace in all_stack_traces:
        print(line_of_trace)


def string_without_apostrophe(any_text: str):
    return any_text.replace('\'', '\\\'')


def iso_datetime(date_object: datetime) -> str:
    if isinstance(date_object, datetime):
        return date_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return date_object


def without_ending_chars(any_text: str, chars: list) -> str:
    """
    Return text without ending chars if it's present
    """
    if any_text:
        new_length = len(any_text)
        for c in reversed(any_text):
            if c in chars:
                new_length -= 1
                continue
            break
        return any_text[:new_length]
    return any_text


def add_to_time(t: datetime.time, delta: timedelta):
    """
    Return new time shifted by delta
    """
    seconds = delta.seconds % 60
    minutes = delta.seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    return time(t.hour + hours, t.minute + minutes, t.second + seconds)


def get_parent_folder_for_file(file_name: str) -> str:
    if not file_name or not os.path.isfile(file_name):
        raise Demo1Error('Argument is not a file')
    return os.path.abspath(str(Path(file_name).parent))


def get_tail_for(baseline: str, separator: str) -> Optional[str]:
    if not baseline:
        return None
    baseline_components = baseline.split(separator)
    return baseline_components[len(baseline_components) - 1]


def replace_tail_for(baseline: str, separator: str, new_tail: str) -> Optional[str]:
    if not baseline or not separator:
        return None
    baseline_components = baseline.split(separator)
    baseline_components[len(baseline_components) - 1] = new_tail
    return separator.join(baseline_components)


def cut_head_separator_for(baseline: str, separator: str) -> Optional[str]:
    if not baseline:
        return None
    baseline_components = baseline.split(separator)
    if not baseline_components[0]:
        return separator.join(baseline_components[1:])
    return separator.join(baseline_components)


def get_file_date(file_datetime: str):
    """
    Return only file_date without time (initial date/time is passed in format '%Y-%m-%d-%H-%M-%S')
    """
    file_time_components = file_datetime.split('-')
    return '-'.join([file_time_components[0], file_time_components[1], file_time_components[2]])


def get_with_the_slash_on_end(file_folder: str):
    """
    Remove final slash if necessary
    """
    result = file_folder
    while result.endswith('/'):
        result = result[:len(result) - 1]
    return result + '/'


def get_iso_datetime(file_datetime: str):
    """
    Convert date/time into server format '%Y-%m-%d-%H-%M-%S.IDENTITY' -> '%Y-%m-%dT%H:%M:%S'
    """
    try:
        time_components = file_datetime.split('-')
        return '%s-%s-%sT%s:%s:%s' % (time_components[0], time_components[1], time_components[2],
                                      time_components[3], time_components[4], time_components[5].split('.')[0])
    except Exception:
        return file_datetime
