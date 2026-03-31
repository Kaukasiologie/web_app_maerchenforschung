from enum import Enum
import time
from pathlib import Path

LogType = Enum('LogType', [('Error', 'ERROR'),
               ('Warning', 'WARNING'), ('Info', 'INFO')])

LOGFILE = Path("viz_server.log")
if LOGFILE:
    LOGFILE.touch()


def log(*args, context='', log_type: LogType = LogType.Info,
        sep=' ', end='\n'):

    stamp = f'{time.asctime()}'

    match(log_type):
        case LogType.Info:
            stamp += f' [{log_type.value}]'
        case LogType.Warning:
            stamp += f' [\033[93m{log_type.value}\033[0m]'
        case LogType.Error:
            stamp += f' [\033[91m{log_type.value}\033[0m]'

    stamp += f' [{context}]'

    if LOGFILE:
        logfile = open(LOGFILE, "a")
    else:
        logfile = None
    print(stamp, *args, sep=sep, end=end, file=logfile)
