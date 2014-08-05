import sys
import time

def convert_relative_time(time_string):
    """Takes a single +XXXX[smhdw] string and converts to seconds"""
    last_char = time_string[len(time_string) - 1]
    user_value = time_string[0:(len(time_string) - 1)]
    if last_char == 's':
        seconds = int(user_value)
    elif last_char == 'm':
        seconds = (int(user_value) * 60)
    elif last_char == 'h':
        seconds = (int(user_value) * 60 * 60)
    elif last_char == 'd':
        seconds = (int(user_value) * 60 * 60 * 24)
    elif last_char == 'w':
        seconds = (int(user_value) * 60 * 60 * 24 * 7)
    else:
        sys.stderr.write("Invalid time format: %s.  "
                "Missing s/m/h/d/w qualifier\n" % (time_string,))
        sys.exit(-1)
    return seconds

def parse_time(time_string, reference_time=int(time.time())):
    """Parses a time in YYYYMMDDHHMMSS or +XXXX[smhdw][...] and returns
    epoch time.  Just like ssk-keygen, we allow complex expressions like
    +5d7h37m for 5 days, 7 hours, 37 minutes.

    reference_time should be the epoch time used for calculating
    the time when using +XXXX[smhdw][...], defaults to now.

    if time_string == 0, returns None"""
    if time_string == '0':
        return None

    seconds = 0
    if time_string[0] == '+' or time_string[0] == '-':
        # parse relative expressions
        sign = None
        number = ''
        factor = 's'
        for c in time_string:
            if not sign:
                sign = c
            elif c.isdigit():
                number = number + c
            else:
                factor = c
                seconds += convert_relative_time(
                        "%s%s%s" % (sign, number, factor))
                number = ''
                factor = 's'

        # per ssh-keygen, if specifing seconds, then the 's' is not required
        if len(number) > 0:
            seconds += convert_relative_time("%s%ss" % (sign, number))

        epoch = seconds + reference_time

    else:
        # parse YYYYMMDDHHMMSS
        struct_time = time.strptime(time_string, "%Y%m%d%H%M%S")
        epoch = int(time.strftime("%s", struct_time))

    return epoch

def epoch2timefmt(epoch):
    """Converts epoch time to YYYYMMDDHHMMSS for ssh-keygen

    ssh-keygen accepts YYYYMMDDHHMMSS in the current TZ but doesn't
    understand DST so it will add an hour for you. :-/
    """
    struct_time = time.localtime(epoch)
    if struct_time.st_isdst == 1:
        struct_time = time.localtime(epoch - 3600)
    return time.strftime("%Y%m%d%H%M%S", struct_time)
