import os
import struct
import unittest
from ssh_ca import agent_client


class TestAgentSocketValidation(unittest.TestCase):

    def test_nonexistent_explicit_path(self):
        self.assertRaises(
            agent_client.SshClientFailure,
            agent_client.Client,
            '/radio/flyer/inchworm/agent.sock'
        )

    def test_nonexistent_env_path(self):
        # don't shoot me for setting an environment variable in a test. I hate
        # myself for it.
        old_env = os.getenv('SSH_AUTH_SOCK')
        try:
            os.environ['SSH_AUTH_SOCK'] = '/eflite/alpha/450/sockeroony.sock'
            self.assertRaises(
                agent_client.SshClientFailure,
                agent_client.Client,
            )
        finally:
            if old_env is not None:
                os.environ['SSH_AUTH_SOCK'] = old_env


class TestAgentBuffer(unittest.TestCase):
    def test_nominal(self):
        # This is a pretty stupid test. But it does touch all of the code in
        # the class and it verifies that everything we shoved in there actually
        # ended up in the serialized string somewhere. Though it may be in the
        # wrong place or not actually correct. Better than nothing?
        buf = agent_client.SshAgentBuffer()
        buf.append_byte(93)
        buf.append_uint32(12394)
        buf.append_string('helloWorld')
        results = buf.serialize()

        self.assertIn(bytes([93]), results)
        self.assertIn(struct.pack('>I', 12394), results)
        self.assertIn(b'helloWorld', results)


if __name__ == '__main__':
    unittest.main()
