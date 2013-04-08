import os
import unittest
import tempfile
import shutil

import badgepad.cmdline

from .test_project import SAMPLE_PROJECT

class BaseSmokeTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        badgepad.cmdline.log = self.log
        self.loglines = []
        self.orig_dir = os.getcwd()

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.dir)

    def log(self, msg):
        self.loglines.append(msg)

    def path(self, *args):
        return os.path.join(self.dir, *args)

    def assertPathExists(self, *args):
        self.assertTrue(os.path.exists(self.path(*args)),
                        'path %s should exist' % '/'.join(args))

class SampleProjectTest(BaseSmokeTest):
    def test(self):
        badgepad.cmdline.main(['--root-dir', SAMPLE_PROJECT, 'build',
                               '--output-dir', self.path('out')])
        self.assertPathExists('out', 'issuer.json')
        self.assertPathExists('out', 'badges', 'img.json')

class ProjectFromScratchTest(BaseSmokeTest):
    def cmdline(self, *args):
        badgepad.cmdline.main(['--root-dir', self.dir] + list(args))

    def test(self):
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

        os.chdir(self.dir)
        self.cmdline('build')
        self.assertTrue("Done. Static website is in 'dist'." in self.loglines)
        self.assertPathExists('dist', 'assertions', 'lol', 'foo.html')
        self.assertPathExists('dist', 'assertions', 'lol', 'foo.json')
        self.assertPathExists('dist', 'badges', 'foo.json')
        self.assertPathExists('dist', 'issuer.json')

        self.cmdline('build')
