import os
import tempfile
import shutil
import unittest
import doctest
from minimock import mock, Mock, restore

from badgepad import server
from badgepad.server import get_dir_state

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite())
    return tests

def test_start_file_server_works():
    """
    >>> import SocketServer
    >>> mock('SocketServer.TCPServer')
    >>> SocketServer.TCPServer.mock_returns = Mock('httpd')
    >>> server.start_file_server('127.0.0.1', 8000)       # doctest: +ELLIPSIS
    Called SocketServer.TCPServer(
        ('127.0.0.1', 8000),
        <class SimpleHTTPServer.SimpleHTTPRequestHandler at ...>)
    serving at port 8000 on 127.0.0.1
    Called httpd.serve_forever()
    >>> restore()
    """

    pass

class ServerTests(unittest.TestCase):
    def testGetDirStateWorks(self):
        tmpdir = tempfile.mkdtemp()
        try:
            state = get_dir_state(tmpdir)
            self.assertEqual(len(state), 32)
            open(os.path.join(tmpdir, 'foo'), 'w').close()
            state2 = get_dir_state(tmpdir)
            self.assertNotEqual(state, state2)
            self.assertEqual(get_dir_state(tmpdir), state2)
            open(os.path.join(tmpdir, '.foo'), 'w').close()
            self.assertEqual(get_dir_state(tmpdir), state2)
            os.mkdir(os.path.join(tmpdir, '.bar'))
            self.assertEqual(get_dir_state(tmpdir), state2)
            os.mkdir(os.path.join(tmpdir, 'bar'))
            open(os.path.join(tmpdir, 'bar', 'baz'), 'w').close()
            self.assertNotEqual(get_dir_state(tmpdir), state2)
        finally:
            shutil.rmtree(tmpdir)
