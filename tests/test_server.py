import os
import tempfile
import shutil
import unittest

from badgepad.server import get_dir_state

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
