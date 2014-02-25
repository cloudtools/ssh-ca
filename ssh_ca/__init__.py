import ConfigParser
import os
import subprocess


__version__ = "0.2.0"


class SSHCAException(Exception):
    pass


class SSHCAInvalidConfiguration(SSHCAException):
    pass


def get_config_value(config, section, name, required=False):
    if config:
        try:
            return config.get(section, name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            if required:
                raise SSHCAInvalidConfiguration(
                    "option '%s' is required in section '%s'" %
                    (name, section))
            pass
    return None


class Authority(object):
    def __init__(self, ca_key):
        self.ca_key = ca_key

    def get_public_key(self, username, environment):
        pass

    def increment_serial_number(self):
        pass

    def make_audit_log(
            self, serial, valid_for, username, ca_key_filename, reason):
        pass

    def upload_public_key(self, username, public_path):
        pass

    def sign_public_key(
            self, public_key_filename, username, expires_in, reason):
        serial = self.increment_serial_number()

        subprocess.check_output([
            'ssh-keygen',
            '-z', str(serial),
            '-s', self.ca_key,
            '-I', username,
            '-V', expires_in,
            '-n', 'ubuntu,ec2-user',
            public_key_filename])

        self.make_audit_log(serial, expires_in, username, self.ca_key, reason)

        if public_key_filename.endswith('.pub'):
            public_key_filename = public_key_filename[:-4]
        cert_filename = public_key_filename + '-cert.pub'
        with open(cert_filename, 'r') as f:
            cert_contents = f.read()
        os.remove(cert_filename)
        return cert_contents
