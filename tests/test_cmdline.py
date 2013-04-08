import os
import unittest
import tempfile
import doctest
import shutil
from minimock import mock, Mock, restore

import badgepad.cmdline

from .test_project import SAMPLE_PROJECT

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite())
    return tests

def test_cmd_serve():
    """
    >>> mock('badgepad.cmdline.start_auto_rebuild_server')
    >>> os.chdir(SAMPLE_PROJECT)
    >>> badgepad.cmdline.main(['serve'])                # doctest: +ELLIPSIS
    Called badgepad.cmdline.start_auto_rebuild_server(
        '...sample-project',
        ip='127.0.0.1',
        port=8000)
    >>> badgepad.cmdline.main(['serve', '-p', '1234', '-i',
    ...                        '1.2.3.4'])              # doctest: +ELLIPSIS
    Called badgepad.cmdline.start_auto_rebuild_server(
        '...sample-project',
        ip='1.2.3.4',
        port=1234)
    >>> restore()
    """

    pass

def test_fail():
    """
    >>> import sys
    >>> mock('sys.exit')
    >>> badgepad.cmdline.fail('oops')
    oops
    Called sys.exit(1)
    >>> restore()
    """

    pass

def test_log():
    """
    >>> badgepad.cmdline.log("hello")
    hello
    """

    pass

class BaseCmdlineTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.old_log = badgepad.cmdline.log
        badgepad.cmdline.log = self.log
        self.loglines = []
        self.orig_dir = os.getcwd()

    def tearDown(self):
        badgepad.cmdline.log = self.old_log
        os.chdir(self.orig_dir)
        shutil.rmtree(self.dir)

    def log(self, msg):
        self.loglines.append(msg)

    def contents(self, *args):
        return open(self.path(*args)).read()

    def path(self, *args):
        return os.path.join(self.dir, *args)

    def assertPathExists(self, *args):
        self.assertTrue(os.path.exists(self.path(*args)),
                        'path %s should exist' % '/'.join(args))

class SampleProjectTest(BaseCmdlineTest):
    def test(self):
        badgepad.cmdline.main(['--root-dir', SAMPLE_PROJECT, 'build',
                               '--output-dir', self.path('out')])
        self.assertPathExists('out', 'issuer.json')
        self.assertPathExists('out', 'badges', 'img.json')

class ProjectFromScratchTest(BaseCmdlineTest):
    def cmdline(self, *args):
        badgepad.cmdline.main(['--root-dir', self.dir] + list(args))

    def assertErr(self, args, msg):
        self.loglines[:] = []
        self.assertRaises(SystemExit, self.cmdline, *args)
        self.assertEqual(self.loglines, [msg])

    def test(self):
        self.assertErr(['serve'], 'Directory does not contain a project.')

        self.cmdline('init')

        self.assertErr(['init'], 'Directory already contains a project.')

        self.cmdline('newbadge', 'foo')
        self.assertTrue('Created badges/foo.yml.' in self.loglines)
        self.assertPathExists('badges', 'foo.yml')

        self.assertErr(['newbadge', 'foo'], 'That badge already exists.')

        cfg = open(self.path('config.yml'), 'a')
        cfg.write('  lol: Lol Person <lol@person.com>\n')
        cfg.close()

        self.cmdline('issue', 'lol', 'foo')
        self.assertTrue('Created assertions/lol.foo.yml.' in self.loglines)

        self.assertErr(['issue', 'a', 'foo'], "Recipient 'a' does not exist.")
        self.assertErr(['issue', 'lol', 'b'], "Badge 'b' does not exist.")
        self.assertErr(['issue', 'lol', 'foo'], 'Badge already issued.')

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

        self.cmdline('build', '-u', 'http://b')
        self.assertTrue('http://b/' in self.contents('dist', 'issuer.json'))
