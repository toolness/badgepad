import os
import glob
import json
import urlparse
import email.utils

import yaml

class Project(object):
    def __init__(self, root_dir):
        self.ROOT = os.path.abspath(root_dir)
        self.DIST_DIR = self.path('dist')
        self.STATIC_DIR = self.path('static')
        self.BADGES_DIR = self.path('badges')
        self.ASSERTIONS_DIR = self.path('assertions')
        self.TEMPLATES_DIR = self.path('templates')
        self.__config = None

    def relpath(self, *filename):
        return os.path.relpath(self.path(*filename), self.ROOT)

    def path(self, *args):
        return os.path.join(self.ROOT, *args)

    def exists(self, *filename):
        return os.path.exists(self.path(*filename))

    def glob(self, *filename):
        return glob.glob(self.path(*filename))

    def listdir(self, *filename):
        return os.listdir(self.path(*filename))

    def absurl(self, url):
        return urlparse.urljoin(self.config['issuer']['url'], url)

    @property
    def config(self):
        if not self.__config:
            config = yaml.load(open(self.path('config.yml')).read())

            for recipient, address in config['recipients'].items():
                parts = email.utils.parseaddr(address)
                config['recipients'][recipient] = {
                    'name': parts[0],
                    'email': parts[1]
                }

            self.__config = config

        return self.__config

    def read_yaml(self, *filename):
        return yaml.load_all(open(self.path(*filename)))

    def write_data(self, data, *filename):
        abspath = self.path(self.DIST_DIR, *filename)
        f = open(abspath, 'w')
        if abspath.endswith('.json'):
            json.dump(data, f, sort_keys=True, indent=True)
        else:
            f.write(data)
        f.close()
