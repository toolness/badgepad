import os
import unittest
import tempfile
import shutil

import badgepad.cmdline

class SmokeTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def cmdline(self, *args):
        badgepad.cmdline.main(['--root-dir', self.dir] + list(args))

    def path(self, *args):
        return os.path.join(self.dir, *args)

    def test_smoke(self):
        self.cmdline('init')
        self.cmdline('newbadge', 'foo')

        cfg = open(self.path('config.yml'), 'a')
        cfg.write('  lol: Lol Person <lol@person.com>\n')
        cfg.close()

        self.cmdline('issue', 'lol', 'foo')
        self.cmdline('build')
