import sys
import time
import unittest

def convert_relative_time(time_string):
    """Takes a single +XXXX[smhdw] string and converts to seconds"""
    last_char = time_string[-1]
    user_value = time_string[0:-1]
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
    """Parses a time in YYYYMMDDHHMMSS or +XXXX[smhdw][...]

    Returns epoch time.  Just like ssk-keygen, we allow complex 
    expressions like +5d7h37m for 5 days, 7 hours, 37 minutes.

    reference_time should be the epoch time used for calculating
    the time when using +XXXX[smhdw][...], defaults to now.
    """

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
        epoch = int(time.mktime(struct_time))

    return epoch

def epoch2timefmt(epoch):
    """Converts epoch time to YYYYMMDDHHMMSS for ssh-keygen

    ssh-keygen accepts YYYYMMDDHHMMSS in the current TZ but doesn't
    understand DST so it will add an hour for you. :-/
    """
    struct_time = time.localtime(epoch)
    if struct_time.tm_isdst == 1:
        struct_time = time.localtime(epoch - 3600)
    return time.strftime("%Y%m%d%H%M%S", struct_time)


class ParseTimeTests(unittest.TestCase):
    def setUp(self):
        self.now = int(time.time())

    def test_one_week(self):
        one_week = parse_time("+1w", self.now)
        one_week_check = self.now + (60 * 60 * 24 * 7)
        self.assertEqual(one_week_check, one_week)

    def test_one_day(self):
        one_day = parse_time("+1d3h15s", self.now)
        one_day_check = self.now + (60 * 60 * 27) + 15
        self.assertEqual(one_day_check, one_day)

    def test_two_thirty(self):
        two_thirty = parse_time("+2h30m", self.now)
        two_thirty_check = self.now + (60 * 60 * 2.5)
        self.assertEqual(two_thirty_check, two_thirty)

    def test_epoch2timefmt(self):
        struct_time = time.localtime(self.now)
        offset = 0
        if struct_time.tm_isdst == 1:
            offset = 3600

        longtime = epoch2timefmt(self.now + offset)
        rightnow = parse_time(longtime)
        self.assertEqual(rightnow, self.now)

if __name__ == '__main__':
    unittest.main()
