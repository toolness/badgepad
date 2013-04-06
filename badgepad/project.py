import os
import glob
import urlparse
import email.utils

import yaml
from markdown import markdown

from .obi import hashed_id

class Bunch:
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

class BadgeAssertions(object):
    def __init__(self, project):
        self.project = project

    def __iter__(self):
        for filename in self.project.glob('assertions', '*.yml'):
            yield BadgeAssertion(self.project, filename)

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return BadgeAssertion(self.project,
                              self.project.path('assertions', '%s.yml' % key))

    def __contains__(self, key):
        return self.project.exists('assertions', '%s.yml' % key)

    def find(self, recipient='*', badge='*'):
        query = '%s.%s.yml' % (recipient, badge)
        for filename in self.project.glob('assertions', query):
            yield BadgeAssertion(self.project, filename)

class BadgeAssertion(object):
    def __init__(self, project, filename):
        self.project = project
        self.filename = filename
        self.basename = os.path.basename(os.path.splitext(filename)[0])
        recipient, badge_class = self.basename.split('.')
        self.recipient = project.config['recipients'][recipient]
        self.badge_class = project.badges[badge_class]

        data = project.read_yaml(filename)
        try:
            json = data.next()
            self.evidence_markdown = data.next()
        except StopIteration:
            self.evidence_markdown = json
            json = {}
        json['uid'] = self.basename
        json['badge'] = self.badge_class.json_url
        if 'issuedOn' not in json:
            json['issuedOn'] = int(os.stat(filename).st_ctime)
        json['recipient'] = hashed_id(self.recipient.email, self.basename)
        json['evidence'] = project.absurl('assertions/%s.html' % \
                                          self.basename)
        json['verify'] = {
            'type': 'hosted',
            'url': project.absurl('assertions/%s.json' % self.basename)
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
            ctx['badge'] = self.badge_class.context
            ctx['recipient'] = self.recipient
            self.__context = ctx
        return self.__context

class BadgeClasses(object):
    def __init__(self, project):
        self.project = project

    def __iter__(self):
        for filename in self.project.glob('badges', '*.yml'):
            yield BadgeClass(self.project, filename)

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return BadgeClass(self.project,
                          self.project.path('badges', '%s.yml' % key))

    def __contains__(self, key):
        return self.project.exists('badges', '%s.yml' % key)

class BadgeClass(object):
    def __init__(self, project, filename):
        self.project = project
        self.filename = filename
        self.basename = os.path.basename(os.path.splitext(filename)[0])
        self.img_filename = project.path('badges', '%s.png' % self.basename)

        data = project.read_yaml(filename)
        json = data.next()
        if os.path.exists(self.img_filename):
            json['image'] = project.absurl('badges/%s.png' % self.basename)
        json['issuer'] = project.absurl('issuer.json')
        json['criteria'] = project.absurl('badges/%s.html' % self.basename)
        self.json_url = project.absurl('badges/%s.json' % self.basename)
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

class Project(object):
    def __init__(self, root_dir):
        self.ROOT = os.path.abspath(root_dir)
        self.STATIC_DIR = self.path('static')
        self.BADGES_DIR = self.path('badges')
        self.ASSERTIONS_DIR = self.path('assertions')
        self.TEMPLATES_DIR = self.path('templates')
        self.__config = None
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

    def absurl(self, url):
        return urlparse.urljoin(self.config['issuer']['url'], url)

    def set_base_url(self, url):
        self.config['issuer']['url'] = url
        if not self.config['issuer']['url'].endswith('/'):
            self.config['issuer']['url'] += '/'

    @property
    def config(self):
        if not self.__config:
            config = yaml.load(self.open('config.yml').read())

            for recipient, address in config['recipients'].items():
                parts = email.utils.parseaddr(address)
                config['recipients'][recipient] = Bunch(name=parts[0],
                                                        email=parts[1])

            self.__config = config
            self.set_base_url(config['issuer']['url'])

        return self.__config

    def read_yaml(self, *filename):
        return yaml.load_all(self.open(*filename))
