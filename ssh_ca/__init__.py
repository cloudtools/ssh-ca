import ConfigParser
import os
import subprocess
import time


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

    def make_audit_log(self,
            serial, valid_for, username, ca_key_filename, reason, principals):
        pass

    def make_host_audit_log(self,
            serial, valid_for, ca_key_filename, reason, hostnames):
        pass

    def upload_public_key(self, username, public_path):
        pass

    def get_host_rsa_key(self, hostname):
        """Gets <hostname>'s public rsa key and returns it."""
        host_pub_key = subprocess.check_output([
            'ssh', hostname,
            'cat', '/etc/ssh/ssh_host_rsa_key.pub'
        ])
        if not host_pub_key.startswith('ssh-rsa'):
            raise ValueError('Unable to get host public key: %s' % (
                host_pub_key,))

        return host_pub_key

    def upload_host_rsa_cert(self, hostname, cert):
        """Puts <cert> into ssh_host_rsa_key-cert.pub on <hostname>"""
        subprocess.check_output([
            'ssh', '-t', hostname,
            'echo "%s" | sudo tee /etc/ssh/ssh_host_rsa_key-cert.pub' % (cert,)
        ])
        host_cert_line = "HostCertificate /etc/ssh/ssh_host_rsa_key-cert.pub"
        subprocess.check_output([
            'ssh', '-t', hostname,
            'echo "%s" | sudo tee -a /etc/ssh/sshd_config' % (host_cert_line,)
        ])
        time.sleep(1)
        subprocess.check_output([
            'ssh', '-t', hostname,
            'sudo service sshd restart'
        ])

    def sign_public_host_key(self,
            public_key_filename, expires_in, hostnames, reason, key_id):
        serial = self.increment_serial_number()

        subprocess.check_output([
            'ssh-keygen',
            '-h',
            '-z', str(serial),
            '-s', self.ca_key,
            '-I', key_id,
            '-V', expires_in,
            '-n', ','.join(hostnames),
            public_key_filename]
        )
        self.make_host_audit_log(
            serial, expires_in, self.ca_key, reason, hostnames)

        return self.get_cert_contents(public_key_filename)

    def sign_public_user_key(self,
            public_key_filename, username, expires_in, reason, principals):
        serial = self.increment_serial_number()

        subprocess.check_output([
            'ssh-keygen',
            '-z', str(serial),
            '-s', self.ca_key,
            '-I', username,
            '-V', expires_in,
            '-n', ','.join(principals),
            public_key_filename]
        )

        self.make_audit_log(
            serial, expires_in, username, self.ca_key, reason, principals)

        return self.get_cert_contents(public_key_filename)

    def get_cert_contents(self, public_key_filename):
        if public_key_filename.endswith('.pub'):
            public_key_filename = public_key_filename[:-4]
        cert_filename = public_key_filename + '-cert.pub'
        with open(cert_filename, 'r') as f:
            cert_contents = f.read()
        os.remove(cert_filename)
        return cert_contents
