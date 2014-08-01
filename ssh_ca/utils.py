import time
import sys

def convert_relative_time(time_string):
    """Takes a single +XXXX[smhdw] string and converts to seconds"""
    last_char = time_string[len(time_string) - 1]
    user_value = time_string[0:(len(time_string) - 1)]
    print time_string
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
    epoch time.  We allow complex expressions like +5d7h for 5 days, 7 hours.

    reference_time should be the epoch time used for calculating
    the time when using +XXXX[smhdw][...]

    if time_string == 0, returns None"""
    if time_string == '0':
        return None

    print("parsing: %s" % (time_string,))
    seconds = 0
    if time_string[0] == '+' or time_string[0] == '-':
        sign = None
        number = ''
        factor = 's'
        for c in time_string:
            print("ts = %s" % (c))
            if not sign:
                sign = c
            elif time_string.isdigit():
                number = number + c
            else:
                factor = c
                seconds += convert_relative_time(
                        "%s%s%s" % (sign, number, factor))
                number = ''
                factor = 's'

        # if specifing seconds, then the 's' is not required
        if len(number) > 0:
            seconds += convert_relative_time("%s%ss" % (sign, number))

        epoch = seconds + reference_time

    else:
        epoch = int(time.strftime("%s",
            time.strptime(time_string, "%Y%m%d%H%M%S")))

    return epoch

def epoch2timefmt(epoch):
    """Converts epoch time to YYYYMMDDHHMMSS"""
    return time.strptime(epoch, "%s").strftime("%Y%m%d%H%M%S")
