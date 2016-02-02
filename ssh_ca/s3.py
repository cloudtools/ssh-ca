import boto.s3
import datetime
import json

from boto.exception import S3ResponseError

import ssh_ca


class S3Authority(ssh_ca.Authority):
    def __init__(self, config, ssh_ca_section, ca_key):
        super(S3Authority, self).__init__(ca_key)

        try:
            # Get a valid S3 bucket
            bucket = ssh_ca.get_config_value(
                config, ssh_ca_section, 'bucket', required=True)

            # Get a valid AWS region
            region = ssh_ca.get_config_value(
                config, ssh_ca_section, 'region', required=True)

            self.s3_conn = boto.s3.connect_to_region(region)
            self.ssh_bucket = self.s3_conn.get_bucket(bucket)
        except S3ResponseError, e:
            if e.code == "AccessDenied":
                raise ssh_ca.SSHCAInvalidConfiguration("Access denied to S3")
            raise

    def increment_serial_number(self):
        k = self.ssh_bucket.get_key('serial')
        if k is None:
            k = self.ssh_bucket.new_key('serial')
            last_serial = 0
        else:
            last_serial = int(k.get_contents_as_string())
        new_serial = last_serial + 1
        k.set_contents_from_string(
            str(int(new_serial)),
            headers={'Content-Type': 'text/json'}
        )
        return new_serial

    def get_public_key(self, username, environment):
        key_names_to_try = [
            'keys/{username}?environment={environment}',
            'keys/{username}'
        ]
        for key_name_template in key_names_to_try:
            key_name = key_name_template.format(
                username=username,
                environment=environment,
            )
            key = self.ssh_bucket.get_key(key_name)
            if key is not None:
                return key.get_contents_as_string()
        else:
            return None

    def upload_public_key(self, username, key_contents):
        k = self.ssh_bucket.new_key('keys/%s' % (username,))
        k.set_contents_from_string(key_contents, replace=True)

    def upload_public_key_cert(self, username, env, cert_contents,
                               expires=7200):
        k = self.ssh_bucket.new_key('certs/%s-%s-cert.pub' % (username, env))
        k.set_contents_from_string(
            cert_contents,
            headers={'Content-Type': 'text/plain'},
            replace=True,
        )
        return k.generate_url(expires)

    def make_host_audit_log(self, serial, valid_for, ca_key_filename,
                            reason, hostnames):
        audit_info = {
            'valid_for': valid_for,
            'access_key': self.s3_conn.access_key,
            'ca_key_filename': ca_key_filename,
            'reason': reason,
            'hostnames': hostnames,
        }
        return self.drop_audit_blob(serial, audit_info)

    def make_audit_log(self, serial, starts_in, expires_in, username,
                       ca_key_filename, reason, principals):
        audit_info = {
            'username': username,
            'valid_for': starts_in + ':' + expires_in,
            'access_key': self.s3_conn.access_key,
            'ca_key_filename': ca_key_filename,
            'reason': reason,
            'principals': principals,
        }
        return self.drop_audit_blob(serial, audit_info)

    def drop_audit_blob(self, serial, blob):
        k = self.ssh_bucket.new_key('audit_log/%d.json' % (serial,))

        timestamp = datetime.datetime.strftime(
            datetime.datetime.utcnow(), '%Y-%m-%d-%H:%M:%S.%f')
        blob['timestamp'] = timestamp

        k.set_contents_from_string(json.dumps(blob))
