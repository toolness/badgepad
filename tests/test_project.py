import os
import unittest

from badgepad.project import Project, BadgeAssertion

path = lambda *x: os.path.join(ROOT, *x)
ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLE_PROJECT = path('sample-project')

def getitem(obj, key):
    return obj[key]

class BadgeClassTests(unittest.TestCase):
    def testKeyErrorIsRaised(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertRaises(KeyError, getitem, proj.badges, 'zzz')

    def testIssuerIsInherited(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.badges['img'].issuer['name'], 'Foo')

    def testNameAndDescriptionAreInherited(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.badges['no-img'].name, 'No Image')
        self.assertEqual(proj.badges['no-img'].description,
                         'This badge has no image associated with it.\n')

    def testWithoutImageWorks(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.badges['no-img'].image_url, None)
        self.assertEqual(proj.badges['no-img'].image_filename, None)
        self.assertTrue('image' not in proj.badges['no-img'].json)

    def testWithImageWorks(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertTrue(proj.badges['img'].image_url)
        self.assertTrue(proj.badges['img'].image_filename)
        self.assertEqual(proj.badges['img'].json['image'],
                         'http://foo.org/badges/img.png')

class FindBadgeAssertionTests(unittest.TestCase):
    def testRecipientAssertionsWorks(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.recipients['foo'].assertions]
        self.assertEqual(len(results), 2)
        self.assertTrue(isinstance(results[0], BadgeAssertion))

    def testBadgeClassAssertionsWorks(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.badges['img'].assertions]
        self.assertEqual(len(results), 1)
        self.assertTrue(isinstance(results[0], BadgeAssertion))

    def testFindByRecipientAndBadgeWorks(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.assertions.find(recipient='foo',
                                                   badge='no-img')]
        self.assertEqual(len(results), 1)

    def testFindByRecipientWorks(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.assertions.find(recipient='foo')]
        self.assertEqual(len(results), 2)

    def testFindByRecipientWorksWithNoResults(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.assertions.find(recipient='zzz')]
        self.assertEqual(len(results), 0)

    def testFindByBadgeWorks(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.assertions.find(badge='no-img')]
        self.assertEqual(len(results), 4)

    def testFindByBadgeWorksWithNoResults(self):
        proj = Project(SAMPLE_PROJECT)
        results = [a for a in proj.assertions.find(badge='zzz')]
        self.assertEqual(len(results), 0)

class BadgeAssertionTests(unittest.TestCase):
    def testKeyErrorIsRaised(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertRaises(KeyError, getitem, proj.assertions, 'zzz')

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
        self.assertTrue('evidence' not in a.json)
        self.assertEqual(a.evidence_url, None)
        self.assertEqual(a.evidence_markdown, None)
        self.assertEqual(a.evidence_html, None)

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

class RecipientTests(unittest.TestCase):
    def testRecipientsAreParsed(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.recipients['foo'].name, 'Foo')
        self.assertEqual(proj.recipients['foo'].email, 'foo@bar.org')

    def testHashedIdentityWorks(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.recipients['foo'].hashed_identity('meh'), {
            'type': 'email',
            'hashed': True,
            'salt': 'meh',
            'identity': 'sha256$b15d735de6ae2152a80de7bdc76eb26215593848' \
                        'cc55ea2c4263b48b9737a9a3'
        })

class ConfigTests(unittest.TestCase):
    def testRecipientsAreNotInConfig(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertTrue('recipients' not in proj.config)

    def testSetBaseUrlAddsSlash(self):
        proj = Project(SAMPLE_PROJECT)
        self.assertEqual(proj.config['issuer']['url'], 'http://foo.org/')
        proj.set_base_url('http://p/blah/')
        self.assertEqual(proj.config['issuer']['url'], 'http://p/blah/')
        proj.set_base_url('http://m/meh')
        self.assertEqual(proj.config['issuer']['url'], 'http://m/meh/')
