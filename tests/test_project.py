import os
import unittest

from badgepad.project import Project

path = lambda *x: os.path.join(ROOT, *x)
ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLE_PROJECT = path('sample-project')

class ProjectTests(unittest.TestCase):
    def testIssuedOnInheritsFromYaml(self):
        proj = Project(SAMPLE_PROJECT)
        issuedOn = proj.assertions['bar.no-img'].json['issuedOn']
        self.assertEqual(issuedOn, 'i am a custom timestamp')

    def testIssuedOnIsUnixTimestampByDefault(self):
        proj = Project(SAMPLE_PROJECT)
        issuedOn = proj.assertions['foo.no-img'].json['issuedOn']
        self.assertTrue(isinstance(issuedOn, int))

    def testRecipientsAreParsed(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.config['recipients']['foo'].name, 'Foo')
        self.assertEqual(proj.config['recipients']['foo'].email,
                         'foo@bar.org')

    def testSetBaseUrlAddsSlash(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.config['issuer']['url'], 'http://foo.org/')
        proj.set_base_url('http://p/blah/')
        self.assertEqual(proj.config['issuer']['url'], 'http://p/blah/')
        proj.set_base_url('http://m/meh')
        self.assertEqual(proj.config['issuer']['url'], 'http://m/meh/')
