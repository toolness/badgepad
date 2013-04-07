import os
import glob
import urlparse
import email.utils
from hashlib import sha256

import yaml
from markdown import markdown

class Recipient(object):
    def __init__(self, project, id, name, email):
        self.project = project
        self.id = id
        self.name = name
        self.email = email

    @property
    def assertions(self):
        return self.project.assertions.find(recipient=self.id)

    def hashed_identity(self, salt):
        idobj = dict(type='email', hashed=True)
        idobj['salt'] = salt
        idobj['identity'] = 'sha256$' + sha256(self.email + salt).hexdigest()
        return idobj

class BadgeAssertion(object):
    def __init__(self, project, filename):
        self.project = project
        self.filename = filename
        self.basename = os.path.basename(os.path.splitext(filename)[0])
        recipient, badge = self.basename.split('.')
        self.recipient = project.recipients[recipient]
        self.badge = project.badges[badge]
        self.paths = {
            'html': ('assertions', recipient, '%s.html' % badge),
            'json': ('assertions', recipient, '%s.json' % badge),
        }

        data = project.read_yaml(filename)
        try:
            json = data.next()
            self.evidence_markdown = data.next()
        except StopIteration:
            self.evidence_markdown = json
            json = {}
        json['uid'] = self.basename
        json['badge'] = self.badge.json_url
        if 'issuedOn' not in json:
            json['issuedOn'] = int(os.stat(filename).st_ctime)
        json['recipient'] = self.recipient.hashed_identity(self.basename)
        json['evidence'] = project.absurl(*self.paths['html'])
        json['verify'] = {
            'type': 'hosted',
            'url': project.absurl(*self.paths['json'])
        }
        self.json = json
        self.__context = None

    @property
    def context(self):
        if not self.__context:
            ctx = {}
            ctx.update(self.json)
            ctx['evidenceHtml'] = markdown(self.evidence_markdown,
                                           output_format='html5')
            ctx['badge'] = self.badge.context
            ctx['recipient'] = self.recipient
            self.__context = ctx
        return self.__context

class BadgeClass(object):
    def __init__(self, project, filename):
        self.project = project
        self.filename = filename
        self.basename = os.path.basename(os.path.splitext(filename)[0])
        self.paths = {
            'png': ('badges', '%s.png' % self.basename),
            'html': ('badges', '%s.html' % self.basename),
            'json': ('badges', '%s.json' % self.basename)
        }
        self.img_filename = project.path(*self.paths['png'])

        data = project.read_yaml(filename)
        json = data.next()
        if os.path.exists(self.img_filename):
            json['image'] = project.absurl(*self.paths['png'])
        json['issuer'] = project.absurl('issuer.json')
        json['criteria'] = project.absurl(*self.paths['html'])
        self.json_url = project.absurl(*self.paths['json'])
        self.json = json

        self.criteria_markdown = data.next()
        self.__context = None

    @property
    def context(self):
        if not self.__context:
            ctx = {}
            ctx.update(self.json)
            ctx['criteriaHtml'] = markdown(self.criteria_markdown,
                                           output_format='html5')
            ctx['url'] = self.json_url
            self.__context = ctx
        return self.__context        

    @property
    def assertions(self):
        return self.project.assertions.find(badge=self.basename)

class YamlCollection(object):
    DIRNAME = None
    CLASS = None

    def __init__(self, project):
        self.project = project

    def __iter__(self):
        for filename in self.project.glob(self.DIRNAME, '*.yml'):
            yield self.CLASS(self.project, filename)

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return self.CLASS(self.project,
                          self.project.path(self.DIRNAME, '%s.yml' % key))

    def __contains__(self, key):
        return self.project.exists(self.DIRNAME, '%s.yml' % key)

class BadgeAssertions(YamlCollection):
    DIRNAME = 'assertions'
    CLASS = BadgeAssertion

    def find(self, recipient='*', badge='*'):
        query = '%s.%s.yml' % (recipient, badge)
        for filename in self.project.glob('assertions', query):
            yield BadgeAssertion(self.project, filename)

class BadgeClasses(YamlCollection):
    DIRNAME = 'badges'
    CLASS = BadgeClass

class Project(object):
    def __init__(self, root_dir):
        self.ROOT = os.path.abspath(root_dir)
        self.STATIC_DIR = self.path('static')
        self.BADGES_DIR = self.path('badges')
        self.ASSERTIONS_DIR = self.path('assertions')
        self.TEMPLATES_DIR = self.path('templates')
        self.__config = None
        self.__recipients = None
        self.badges = BadgeClasses(self)
        self.assertions = BadgeAssertions(self)

    def relpath(self, *filename):
        return os.path.relpath(self.path(*filename), self.ROOT)

    def path(self, *args):
        return os.path.join(self.ROOT, *args)

    def exists(self, *filename):
        return os.path.exists(self.path(*filename))

    def glob(self, *filename):
        return glob.glob(self.path(*filename))

    def open(self, *filename):
        return open(self.path(*filename))

    def absurl(self, *url):
        url = '/'.join(url)
        return urlparse.urljoin(self.config['issuer']['url'], url)

    def set_base_url(self, url):
        self.config['issuer']['url'] = url
        if not self.config['issuer']['url'].endswith('/'):
            self.config['issuer']['url'] += '/'

    @property
    def recipients(self):
        if self.__recipients is None:
            # This triggers the setting of self.__recipients.
            self.config
        return self.__recipients

    @property
    def config(self):
        if not self.__config:
            config = yaml.load(self.open('config.yml').read())

            recipients = {}
            for slug, address in config['recipients'].items():
                parts = email.utils.parseaddr(address)
                recipient = Recipient(self, slug, parts[0], parts[1])
                recipients[slug] = recipient
            del config['recipients']

            self.__config = config
            self.__recipients = recipients
            self.set_base_url(config['issuer']['url'])

        return self.__config

    def read_yaml(self, *filename):
        return yaml.load_all(self.open(*filename))
