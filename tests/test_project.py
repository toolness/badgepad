import os
import unittest

from badgepad.project import Project

path = lambda *x: os.path.join(ROOT, *x)
ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLE_PROJECT = path('sample-project')

class BadgeAssertionTests(unittest.TestCase):
    def testYamlWithoutMetadataWorks(self):
        proj = Project(SAMPLE_PROJECT)
        a = proj.assertions['foo.no-img']
        self.assertTrue(a.json)
        self.assertEquals(a.evidence_markdown, "no metadata here.")

    def testYamlWithMetadataWorks(self):
        proj = Project(SAMPLE_PROJECT)
        a = proj.assertions['bar.no-img']
        self.assertTrue(a.json)
        self.assertEquals(a.evidence_markdown, "some metadata here.")

    def testYamlWithoutMetadataOrEvidenceWorks(self):
        proj = Project(SAMPLE_PROJECT)
        a = proj.assertions['baz.no-img']
        self.assertTrue(a.json)
        self.assertEqual(a.evidence_markdown, None)

    def testYamlWithMetadataButNoEvidenceWorks(self):
        proj = Project(SAMPLE_PROJECT)
        a = proj.assertions['quux.no-img']
        self.assertEqual(a.json['blah'], 'hello')
        self.assertEqual(a.evidence_markdown, None)

    def testIssuedOnInheritsFromYaml(self):
        proj = Project(SAMPLE_PROJECT)
        issuedOn = proj.assertions['bar.no-img'].json['issuedOn']
        self.assertEqual(issuedOn, 'i am a custom timestamp')

    def testIssuedOnIsUnixTimestampByDefault(self):
        proj = Project(SAMPLE_PROJECT)
        issuedOn = proj.assertions['foo.no-img'].json['issuedOn']
        self.assertTrue(isinstance(issuedOn, int))

class ConfigTests(unittest.TestCase):
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
