from setuptools import setup

setup(
    name='Badgepad',
    version='0.1.0',
    author='Atul Varma',
    author_email='varmaa@gmail.com',
    packages=['badgepad'],
    scripts=['bin/badgepad'],
    url='http://pypi.python.org/pypi/Badgepad/',
    license='LICENSE.txt',
    description='Issue Open Badges as static files.',
    long_description=open('README.rst').read(),
    install_requires=open('requirements.txt').readlines()
)
