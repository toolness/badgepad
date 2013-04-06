import unittest

from mock import patch, mock_open

from badgepad.project import Project

CFG_YML = """\
issuer:
  url: http://foo.org
recipients:
  foo: Foo <foo@bar.org>
"""

class ProjectTests(unittest.TestCase):
    @patch('badgepad.project.open', mock_open(read_data=CFG_YML), create=True)
    def testRecipientsAreParsed(self):
        proj = Project('.')
        self.assertEqual(proj.config['recipients']['foo'].name, 'Foo')
        self.assertEqual(proj.config['recipients']['foo'].email,
                         'foo@bar.org')

    @patch('badgepad.project.open', mock_open(read_data=CFG_YML), create=True)
    def testSetBaseUrlAddsSlash(self):
        proj = Project('.')
        self.assertEqual(proj.config['issuer']['url'], 'http://foo.org/')
        proj.set_base_url('http://p/blah/')
        self.assertEqual(proj.config['issuer']['url'], 'http://p/blah/')
        proj.set_base_url('http://m/meh')
        self.assertEqual(proj.config['issuer']['url'], 'http://m/meh/')
