import os
import unittest
import tempfile
import shutil

import badgepad.cmdline

class SmokeTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        badgepad.cmdline.log = self.log
        self.loglines = []

    def tearDown(self):
        shutil.rmtree(self.dir)

    def log(self, msg):
        self.loglines.append(msg)

    def cmdline(self, *args):
        badgepad.cmdline.main(['--root-dir', self.dir] + list(args))

    def path(self, *args):
        return os.path.join(self.dir, *args)

    def assertPathExists(self, *args):
        self.assertTrue(os.path.exists(self.path(*args)),
                        'path %s exists' % '/'.join(args))

    def test_smoke(self):
        self.cmdline('init')
        self.cmdline('newbadge', 'foo')
        self.assertTrue('Created badges/foo.yml.' in self.loglines)
        self.assertPathExists('badges', 'foo.yml')

        cfg = open(self.path('config.yml'), 'a')
        cfg.write('  lol: Lol Person <lol@person.com>\n')
        cfg.close()

        self.cmdline('issue', 'lol', 'foo')
        self.assertTrue('Created assertions/lol.foo.yml.' in self.loglines)

        assertion = open(self.path('assertions', 'lol.foo.yml'), 'a')
        assertion.write(u'o yea \u2026'.encode('utf-8'))
        assertion.close()

        self.cmdline('build')
        self.assertPathExists('dist', 'assertions', 'lol', 'foo.html')
        self.assertPathExists('dist', 'assertions', 'lol', 'foo.json')
        self.assertPathExists('dist', 'badges', 'foo.json')
        self.assertPathExists('dist', 'issuer.json')
