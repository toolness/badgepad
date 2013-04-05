import os
import sys
import shutil
import json
import argparse

import jinja2
import markdown

from .obi import hashed_id
from .project import Project

def log(text):
    sys.stdout.write(text + '\n')

def pkg_path(*args):
    return os.path.join(PKG_ROOT, *args)

PKG_ROOT = os.path.dirname(os.path.abspath(__file__))

class UnknownBadgeError(KeyError):
    pass

class UnknownRecipientError(KeyError):
    pass

def write_data(data, *filename):
    abspath = os.path.join(*filename)
    f = open(abspath, 'w')
    if abspath.endswith('.json'):
        json.dump(data, f, sort_keys=True, indent=True)
    else:
        f.write(data)
    f.close()

def process_assertions(project, jinja_env, badge_classes, dest_dir):
    dest_dir = os.path.join(dest_dir, 'assertions')
    issuer = project.config['issuer']
    recipients = project.config['recipients']

    template = jinja_env.get_template('assertion.html')
    os.mkdir(dest_dir)
    for filename in project.listdir('assertions'):
        abspath = project.path('assertions', filename)
        data = project.read_yaml(abspath)
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
        metadata['evidence'] = project.absurl('/assertions/%s.html' % basename)
        metadata['verify'] = {
            'type': 'hosted',
            'url': project.absurl('/assertions/%s.json' % basename)
        }
        write_data(metadata, dest_dir, '%s.json' % basename)

        context = {}
        context.update(metadata)
        context['badge'] = badge_class
        context['recipient'] = recipients[recipient]
        context['evidenceHtml'] = markdown.markdown(evidence_markdown,
                                                    output_format='html5')
        evidence_html = template.render(**context)
        write_data(evidence_html, dest_dir, '%s.html' % basename)

def process_badge_classes(project, jinja_env, dest_dir):
    dest_dir = os.path.join(dest_dir, 'badges')
    issuer = project.config['issuer']

    classes = {}
    template = jinja_env.get_template('badge.html')
    os.mkdir(dest_dir)
    for filename in project.glob('badges', '*.yml'):
        basename = os.path.basename(os.path.splitext(filename)[0])
        img_filename = project.path('badges', '%s.png' % basename)
        data = project.read_yaml(filename)
        metadata = data.next()
        if os.path.exists(img_filename):
            metadata['image'] = project.absurl('/badges/%s.png' % basename)
            shutil.copy(img_filename, dest_dir)
        metadata['issuer'] = project.absurl('/issuer.json')
        metadata['criteria'] = project.absurl('/badges/%s.html' % basename)
        write_data(metadata, dest_dir, '%s.json' % basename)

        context = {}
        context.update(metadata)
        context['criteriaHtml'] = markdown.markdown(data.next(),
                                                    output_format='html5')
        context['url'] = project.absurl('/badges/%s.json' % basename)
        classes[basename] = context
        criteria_html = template.render(**context)
        write_data(criteria_html, dest_dir, '%s.html' % basename)
    return classes

def cmd_build(project, args):
    """
    Build website.
    """

    loader = jinja2.FileSystemLoader(project.TEMPLATES_DIR)
    env = jinja2.Environment(loader=loader)
    dest_dir = project.path('dist')

    if os.path.exists(dest_dir):
        log("Removing %s." % dest_dir)
        shutil.rmtree(dest_dir)

    log("Copying static files.")
    shutil.copytree(project.STATIC_DIR, dest_dir)

    write_data(project.config['issuer'], dest_dir, 'issuer.json')

    log("Processing badge classes.")
    badge_classes = process_badge_classes(project, env, dest_dir)

    log("Processing assertions.")
    process_assertions(project, env, badge_classes, dest_dir)

    log("Done. Static website is in the '%s' dir." % project.relpath('dist'))

def cmd_init(project, args):
    """
    Initialize new project directory.
    """

    if project.exists('config.yml'):
        log("The current directory already contains a project.")
        sys.exit(1)

    log("Generating config.yml.")
    shutil.copy(pkg_path('samples', 'config.yml'), project.ROOT)

    log("Creating empty directories.")
    os.mkdir(project.path('assertions'))
    os.mkdir(project.path('badges'))
    os.mkdir(project.path('static'))

    log("Creating default templates.")
    shutil.copytree(pkg_path('samples', 'templates'), project.TEMPLATES_DIR)

    log("Done.")

def cmd_newbadge(project, args):
    """
    Create a new badge type.
    """

    filename = project.path('badges', '%s.yml' % args.name)
    if os.path.exists(filename):
        log("That badge already exists.")
        sys.exit(1)

    shutil.copy(pkg_path('samples', 'badge.yml'), filename)
    log("Created %s." % project.relpath(filename))

    pngfile = project.relpath('badges', '%s.png' % args.name)
    log("To give the badge an image, copy a PNG file to %s." % pngfile)

def cmd_issue(project, args):
    """
    Issue a badge to a recipient.
    """

    basename = '%s.%s' % (args.recipient, args.badge)
    filename = project.path('assertions', '%s.yml' % basename)

    if not project.exists('badges', '%s.yml' % args.badge):
        log("The badge '%s' does not exist." % args.badge)
        sys.exit(1)

    if args.recipient not in project.config['recipients']:
        log("The recipient '%s' does not exist." % args.recipient)
        sys.exit(1)

    if os.path.exists(filename):
        log("That badge has already been issued to that recipient.")
        sys.exit(1)

    shutil.copy(pkg_path('samples', 'assertion.yml'), filename)
    log("Created %s." % project.relpath(filename))

def main(arglist=None):
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--root-dir', help='root project directory',
                        default='.')

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

    args = parser.parse_args(arglist)
    args.func(Project(args.root_dir), args)
