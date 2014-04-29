import base64
import os
import socket
import struct

SSH_AGENT_FAILURE = 5
SSH_AGENT_SUCCESS = 6
SSH_AGENTC_REMOVE_RSA_IDENTITY = 18


class SshClientFailure(Exception):
    pass


class SshAgentBuffer(object):
    def __init__(self):
        self.parts = []

    def append_byte(self, byte):
        self.parts.append(chr(byte))

    def append_uint32(self, number):
        self.parts.append(struct.pack('>I', number))

    def append_string(self, string):
        self.append_uint32(len(string))
        self.parts.append(string)

    def serialize(self):
        resultant_buffer = ''.join(self.parts)
        return struct.pack('>I', len(resultant_buffer)) + resultant_buffer


class Client(object):
    def __init__(self, ssh_agent_sock_path=None):
        self.connection = None
        self.ssh_agent_sock_path = ssh_agent_sock_path

    def connect(self):
        self.connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if self.ssh_agent_sock_path is None:
            self.ssh_agent_sock_path = os.getenv('SSH_AUTH_SOCK')
        self.connection.connect(self.ssh_agent_sock_path)

    def _send_msg(self, msg):
        self.connection.sendall(msg)

    def _recv_exact(self, count):
        result_buffer = ''
        while len(result_buffer) < count:
            result_buffer += self.connection.recv(count - len(result_buffer))
        return result_buffer

    def _recv_msg(self):
        response_size = self._recv_exact(4)
        response_size = struct.unpack('>I', response_size)[0]

        response = self._recv_exact(response_size)
        return response

    def _recv_response_code(self):
        response = self._recv_msg()
        if len(response) != 1:
            raise ValueError('Unexpected response length from server')
        return struct.unpack('B', response)[0]

    def remove_key(self, pubkey):
        remove_msg = SshAgentBuffer()
        remove_msg.append_byte(SSH_AGENTC_REMOVE_RSA_IDENTITY)
        remove_msg.append_string(base64.b64decode(pubkey))
        self._send_msg(remove_msg.serialize())
        if SSH_AGENT_SUCCESS != self._recv_response_code():
            raise SshClientFailure('Unable to remove key.')
