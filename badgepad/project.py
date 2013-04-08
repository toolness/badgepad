import os
import glob
import urlparse
import email.utils
import re
from hashlib import sha256

import yaml
from markdown import markdown

def pathify(urlpattern, **context):
    """
    Converts a url pattern-esque string into a path, given a context
    dict, and splits the result.

    Example:

        >>> pathify('/a/:foo/:bar.xml', foo='beets', bar='eggs')
        ('a', 'beets', 'eggs.xml')
    """

    repl = lambda match: context[match.group(1)]
    path = re.sub(r':([a-z]+)', repl, urlpattern)
    return tuple(path[1:].split('/'))

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
            'html': pathify(project.config['urlmap']['evidence'],
                            recipient=recipient, badge=badge),
            'json': pathify(project.config['urlmap']['assertion'],
                            recipient=recipient, badge=badge),
        }
        self.evidence_url = project.absurl(*self.paths['html'])
        self.json_url = project.absurl(*self.paths['json'])

        data = project.read_yaml(filename)
        try:
            json = data.next()
            self.evidence_markdown = data.next()
        except StopIteration:
            self.evidence_markdown = json
            json = {}

        if not self.evidence_markdown:
            self.evidence_url = None
        else:
            json['evidence'] = self.evidence_url

        json['uid'] = self.basename
        json['badge'] = self.badge.json_url
        if 'issuedOn' not in json:
            json['issuedOn'] = int(os.stat(filename).st_ctime)
        json['recipient'] = self.recipient.hashed_identity(self.basename)
        json['verify'] = {
            'type': 'hosted',
            'url': self.json_url
        }
        self.json = json
        self.__evidence_html = None

    @property
    def evidence_html(self):
        if self.evidence_markdown and (not self.__evidence_html):
            self.__evidence_html = markdown(self.evidence_markdown,
                                            output_format='html5')
        return self.__evidence_html

class BadgeClass(object):
    def __init__(self, project, filename):
        self.project = project
        self.filename = filename
        self.basename = os.path.basename(os.path.splitext(filename)[0])
        self.paths = {
            'png': pathify(project.config['urlmap']['image'],
                           badge=self.basename),
            'html': pathify(project.config['urlmap']['criteria'],
                            badge=self.basename),
            'json': pathify(project.config['urlmap']['badge'],
                            badge=self.basename)
        }
        self.image_filename = os.path.splitext(filename)[0] + '.png'
        self.image_url = project.absurl(*self.paths['png'])
        self.issuer = project.config['issuer']
        self.criteria_url = project.absurl(*self.paths['html'])

        data = project.read_yaml(filename)
        json = data.next()
        if os.path.exists(self.image_filename):
            json['image'] = self.image_url
        else:
            self.image_filename = None
            self.image_url = None
        json['issuer'] = project.absurl(*project.paths['json'])
        json['criteria'] = self.criteria_url
        self.json_url = project.absurl(*self.paths['json'])
        self.json = json
        self.name = json.get('name')
        self.description = json.get('description')

        self.criteria_markdown = data.next()
        self.__criteria_html = None

    @property
    def criteria_html(self):
        if not self.__criteria_html:
            self.__criteria_html = markdown(self.criteria_markdown,
                                            output_format='html5')
        return self.__criteria_html

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
    def paths(self):
        return {'json': pathify(self.config['urlmap']['issuer'])}

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
