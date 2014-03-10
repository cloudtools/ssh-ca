import datetime
import json
import sqlite3

import ssh_ca


class SqliteAuthority(ssh_ca.Authority):
    def __init__(self, config, ssh_ca_section, ca_key):
        super(SqliteAuthority, self).__init__(ca_key)

        self.dbfile = ssh_ca.get_config_value(
            config, ssh_ca_section, 'dbfile', required=True)
        self.conn = sqlite3.connect(self.dbfile)
        self._check_schema()

    def _check_schema(self):
        version = self.conn.execute('PRAGMA user_version').fetchone()
        if version[0] == 0:
            with self.conn:
                self.conn.execute('PRAGMA user_version=1')
                self.conn.execute(
                    'create table keys (name, environment, public_key)')
                self.conn.execute(
                    'create table serial (row, serial integer)')
                self.conn.execute(
                    'create table audit_log (entry integer primary key, log)')
                self.conn.execute(
                    'insert into serial (row, serial) values (1, 0)')

    def increment_serial_number(self):
        with self.conn:
            self.conn.execute('update serial set serial=serial+1 where row=1')
        cur = self.conn.execute('select serial from serial where row=1')
        new_serial = cur.fetchone()[0]
        return new_serial

    def get_public_key(self, username, environment):
        select = 'select public_key from keys where name is ?'
        args = (username, )
        cur = self.conn.execute(select, args)
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            return None

    def upload_public_key(self, username, key_file):
        key = open(key_file).read()
        arglist = (username, key)
        insert_stmt = 'insert into keys (name, public_key) values (?, ?)'
        with self.conn:
            self.conn.execute(insert_stmt, arglist)

    def upload_public_key_cert(self, username, cert_contents):
        return "%s: %s" % (username, cert_contents)

    def make_host_audit_log(self, serial, valid_for, ca_key_filename,
                            reason, hostnames):
        audit_info = {
            'valid_for': valid_for,
            'ca_key_filename': ca_key_filename,
            'reason': reason,
            'hostnames': hostnames,
        }
        return self.drop_audit_blob(serial, audit_info)

    def make_audit_log(self, serial, valid_for, username,
                       ca_key_filename, reason, principals):
        audit_info = {
            'username': username,
            'valid_for': valid_for,
            'ca_key_filename': ca_key_filename,
            'reason': reason,
            'principals': principals,
        }
        return self.drop_audit_blob(serial, audit_info)

    def drop_audit_blob(self, serial, blob):
        timestamp = datetime.datetime.strftime(
            datetime.datetime.utcnow(), '%Y-%m-%d-%H:%M:%S.%f')
        blob['serial'] = serial
        blob['timestamp'] = timestamp

        arglist = (None, json.dumps(blob))
        with self.conn:
            self.conn.execute('insert into audit_log values (?, ?)', arglist)
