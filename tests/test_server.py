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

def test_start_auto_rebuild_server():
    """
    >>> import threading
    >>> import time
    >>> mock('threading.Thread', returns=Mock('thread'))
    >>> mock('time.sleep')
    >>> mock('tempfile.mkdtemp', returns='temp')
    >>> mock('os.chdir')
    >>> mock('server.auto_rebuilder', returns=[1, 2])
    >>> mock('shutil.rmtree')
    >>> mock('os.path.exists', returns=True)

    >>> server.start_auto_rebuild_server(
    ...     'root',
    ...     '127.0.0.1',
    ...     3000
    ... )                                                # doctest: +ELLIPSIS
    Called tempfile.mkdtemp()
    Called threading.Thread(
        kwargs={'ip': '127.0.0.1', 'port': 3000},
        target=<function start_file_server at ...>)
    Called thread.start()
    Called server.auto_rebuilder('root', 'temp')
    Called os.chdir('temp')
    Called time.sleep(1)
    Called os.chdir('temp')
    Called time.sleep(1)
    Called os.path.exists('temp')
    Called shutil.rmtree('temp')

    >>> restore()
    """

    pass

def test_auto_rebuilder():
    """
    >>> mock('server.build_website')
    >>> mock('server.get_dir_state', returns='abc')
    >>> mock('server.Project', returns='proj')

    >>> ar = server.auto_rebuilder('root', 'dest')
    >>> ar.next()
    Called server.get_dir_state('root')
    rebuilding website... Called server.Project('root')
    Called server.build_website('proj', dest_dir='dest')
    done.

    >>> ar.next()
    Called server.get_dir_state('root')

    >>> server.get_dir_state.mock_returns = 'def'
    >>> server.build_website.mock_raises = Exception('hmph')
    >>> ar.next()                                        # doctest: +ELLIPSIS
    Called server.get_dir_state('root')
    rebuilding website... Called server.Project('root')
    Called server.build_website('proj', dest_dir='dest')
    Traceback (most recent call last):
    ...
    Exception: hmph

    >>> server.get_dir_state.mock_returns = 'ghi'
    >>> server.build_website.mock_raises = None
    >>> ar.next()
    Called server.get_dir_state('root')
    rebuilding website... Called server.Project('root')
    Called server.build_website('proj', dest_dir='dest')
    done.

    >>> restore()
    """

    pass

def test_start_file_server_works():
    """
    >>> import SocketServer
    >>> mock('SocketServer.TCPServer')
    >>> SocketServer.TCPServer.mock_returns = Mock('httpd')
    >>> server.start_file_server('127.0.0.1', 8000)     # doctest: +ELLIPSIS
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
