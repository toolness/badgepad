import sys
import subprocess
from setuptools import setup, Command

class CoverageTest(Command):
    MIN_COVERAGE=100

    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        errno = subprocess.call([
            'coverage', 'run',
            '--source', 'badgepad',
            '-m', 'unittest', 'discover'
        ])
        if errno: raise SystemExit(errno)
        errno = subprocess.call([
            'coverage', 'report',
            '--fail-under', str(self.MIN_COVERAGE), '-m'
        ])
        if not errno:
            print "All tests succeeded with "\
                  "at least %d%% code coverage." % self.MIN_COVERAGE
        raise SystemExit(errno)

setup(
    name='Badgepad',
    version='0.1.0',
    author='Atul Varma',
    author_email='varmaa@gmail.com',
    packages=['badgepad'],
    scripts=['bin/badgepad'],
    cmdclass = {'test': CoverageTest},
    url='http://pypi.python.org/pypi/Badgepad/',
    license='LICENSE.txt',
    description='Issue Open Badges as static files.',
    install_requires=open('requirements.txt').readlines()
)
