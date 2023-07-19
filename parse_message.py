import re
from time_constants import TIME_CONSTANTS

remind_me_regex = "^(R|r)emind (me|@[\w]+) in "
numeral_regex = "^\d+"
class Task:
    def __init__(self, numeral, time_type, task):
        self.numeral = numeral
        self.time_type = time_type
        self.task = task


def get_time_type(word):
    for time_type, option in TIME_CONSTANTS.items():
        if word in option:
            return time_type
    return None


def parse_message(msg):
    try:
        remind_chunk = re.search(remind_me_regex, msg)
        if not remind_chunk:
            raise ValueError("Error parsing 'Remind me' or 'Remind @user'")
        numeral_chunk = re.search(numeral_regex, msg[remind_chunk.span()[1]:])
        if not numeral_chunk:
            raise ValueError("Error parsing interval")
        span = remind_chunk.span()[1] + numeral_chunk.span()[1]
        numeral_chunk = int(numeral_chunk.group())
        time_type_chunk = msg[span:].strip().split(" ", 1)[0]
        time_type = get_time_type(time_type_chunk)
        if not time_type:
            raise ValueError("Error parsing time type")
        task_chunk = msg[span:].strip().split(" ", 1)[1]
        task_chunk = task_chunk.strip().split("to")[1].strip()
        cleaned_task = Task(numeral_chunk, time_type, task_chunk)
        return cleaned_task
    except ValueError as err:
        print(err)
        return None
