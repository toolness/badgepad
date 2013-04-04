import os
import sys
import shutil
import json
import glob
import hashlib
import argparse
import email.utils
from urlparse import urljoin

import jinja2
import yaml
import markdown

def pkg_path(*args):
    return os.path.join(PKG_ROOT, *args)

def path(*args):
    return os.path.join(ROOT, *args)

def relpath(abspath):
    return os.path.relpath(abspath, ROOT)

PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.getcwd())
DIST_DIR = path('dist')
STATIC_DIR = path('static')
BADGES_DIR = path('badges')
ASSERTIONS_DIR = path('assertions')
TEMPLATES_DIR = path('templates')

class UnknownBadgeError(KeyError):
    pass

class UnknownRecipientError(KeyError):
    pass

def write_data(data, *filename):
    abspath = path(DIST_DIR, *filename)
    f = open(abspath, 'w')
    if abspath.endswith('.json'):
        json.dump(data, f, sort_keys=True, indent=True)
    else:
        f.write(data)
    f.close()

def hashed_id(recipient, salt):
    email = recipient['email']
    idobj = {
        'type': 'email',
        'hashed': True
    }
    idobj['salt'] = salt
    idobj['identity'] = 'sha256$' + hashlib.sha256(email + salt).hexdigest()
    return idobj

def process_assertions(jinja_env, issuer, recipients, badge_classes):
    absurl = lambda x: urljoin(issuer['url'], x)

    template = jinja_env.get_template('assertion.html')
    assertions_dir = path(DIST_DIR, 'assertions')
    os.mkdir(assertions_dir)
    for filename in os.listdir(ASSERTIONS_DIR):
        abspath = path(ASSERTIONS_DIR, filename)
        data = yaml.load_all(open(abspath))
        try:
            metadata = data.next()
            evidence_markdown = data.next()
        except StopIteration:
            evidence_markdown = metadata
            metadata = {}
        basename = os.path.splitext(filename)[0]
        recipient, badge_class = basename.split('.')
        if badge_class not in badge_classes:
            raise UnknownBadgeError(badge_class)
        if recipient not in recipients:
            raise UnknownRecipientError(recipient)
        badge_class = badge_classes[badge_class]
        metadata['uid'] = basename
        metadata['badge'] = badge_class['url']
        if 'issuedOn' not in metadata:
            metadata['issuedOn'] = int(os.stat(abspath).st_ctime)
        metadata['recipient'] = hashed_id(recipients[recipient], basename)
        metadata['evidence'] = absurl('/assertions/%s.html' % basename)
        metadata['verify'] = {
            'type': 'hosted',
            'url': absurl('/assertions/%s.json' % basename)
        }
        write_data(metadata, assertions_dir, '%s.json' % basename)

        context = {}
        context.update(metadata)
        context['badge'] = badge_class
        context['recipient'] = recipients[recipient]
        context['evidenceHtml'] = markdown.markdown(evidence_markdown,
                                                    output_format='html5')
        evidence_html = template.render(**context)
        write_data(evidence_html, assertions_dir, '%s.html' % basename)

def process_badge_classes(jinja_env, issuer):
    absurl = lambda x: urljoin(issuer['url'], x)

    classes = {}
    template = jinja_env.get_template('badge.html')
    badges_dir = path(DIST_DIR, 'badges')
    os.mkdir(badges_dir)
    for filename in glob.glob(path(BADGES_DIR, '*.yml')):
        basename = os.path.basename(os.path.splitext(filename)[0])
        img_filename = path(BADGES_DIR, '%s.png' % basename)
        data = yaml.load_all(open(filename))
        metadata = data.next()
        if os.path.exists(img_filename):
            metadata['image'] = absurl('/badges/%s.png' % basename)
            shutil.copy(img_filename, badges_dir)
        metadata['issuer'] = absurl('/issuer.json')
        metadata['criteria'] = absurl('/badges/%s.html' % basename)
        write_data(metadata, badges_dir, '%s.json' % basename)

        context = {}
        context.update(metadata)
        context['criteriaHtml'] = markdown.markdown(data.next(),
                                                    output_format='html5')
        context['url'] = absurl('/badges/%s.json' % basename)
        classes[basename] = context
        criteria_html = template.render(**context)
        write_data(criteria_html, badges_dir, '%s.html' % basename)
    return classes

def load_config():
    config = yaml.load(open('config.yml').read())

    for recipient, address in config['recipients'].items():
        parts = email.utils.parseaddr(address)
        config['recipients'][recipient] = {
            'name': parts[0],
            'email': parts[1]
        }

    return config

def cmd_build(args):
    """
    Build website.
    """

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))
    config = load_config()

    if os.path.exists(DIST_DIR):
        print "Removing existing '%s' dir." % relpath(DIST_DIR)
        shutil.rmtree(DIST_DIR)

    print "Copying static files."
    shutil.copytree(STATIC_DIR, DIST_DIR)

    write_data(config['issuer'], 'issuer.json')

    print "Processing badge classes."
    badge_classes = process_badge_classes(env, config['issuer'])

    print "Processing assertions."
    process_assertions(env, config['issuer'],
                       config['recipients'], badge_classes)

    print "Done. Static website is in the '%s' dir." % relpath(DIST_DIR)

def cmd_init(args):
    """
    Initialize new project directory.
    """

    if os.path.exists(path('config.yml')):
        print "The current directory already contains a project."
        sys.exit(1)

    print "Generating config.yml."
    shutil.copy(pkg_path('samples', 'config.yml'), ROOT)

    print "Creating empty directories."
    os.mkdir(path('assertions'))
    os.mkdir(path('badges'))
    os.mkdir(path('static'))

    print "Creating default templates."
    shutil.copytree(pkg_path('samples', 'templates'), TEMPLATES_DIR)

    print "Done."

def cmd_newbadge(args):
    """
    Create a new badge type.
    """

    filename = path(BADGES_DIR, '%s.yml' % args.name)
    if os.path.exists(filename):
        print "That badge already exists."
        sys.exit(1)

    shutil.copy(pkg_path('samples', 'badge.yml'), filename)
    print "Created %s." % relpath(filename)

    pngfile = relpath(path(BADGES_DIR, '%s.png' % args.name))
    print "To give the badge an image, copy a PNG file to %s." % pngfile

def cmd_issue(args):
    """
    Issue a badge to a recipient.
    """

    basename = '%s.%s' % (args.recipient, args.badge)
    filename = path(ASSERTIONS_DIR, '%s.yml' % basename)

    if not os.path.exists(path(BADGES_DIR, '%s.yml' % args.badge)):
        print "The badge '%s' does not exist." % args.badge
        sys.exit(1)

    if args.recipient not in load_config()['recipients']:
        print "The recipient '%s' does not exist." % args.recipient
        sys.exit(1)

    if os.path.exists(filename):
        print "That badge has already been issued to that recipient."
        sys.exit(1)

    shutil.copy(pkg_path('samples', 'assertion.yml'), filename)
    print "Created %s." % relpath(filename)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    build = subparsers.add_parser('build', help=cmd_build.__doc__)
    build.set_defaults(func=cmd_build)

    init = subparsers.add_parser('init', help=cmd_init.__doc__)
    init.set_defaults(func=cmd_init)

    newbadge = subparsers.add_parser('newbadge', help=cmd_newbadge.__doc__)
    newbadge.add_argument('name')
    newbadge.set_defaults(func=cmd_newbadge)

    issue = subparsers.add_parser('issue', help=cmd_issue.__doc__)
    issue.add_argument('recipient')
    issue.add_argument('badge')
    issue.set_defaults(func=cmd_issue)

    args = parser.parse_args()
    args.func(args)
