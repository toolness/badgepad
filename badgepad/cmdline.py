import os
import sys
import shutil
import json
import argparse

import jinja2

from .project import Project

def log(text):
    sys.stdout.write(text + '\n')

def pkg_path(*args):
    return os.path.join(PKG_ROOT, *args)

PKG_ROOT = os.path.dirname(os.path.abspath(__file__))

def write_data(data, *filename):
    abspath = os.path.join(*filename)
    f = open(abspath, 'w')
    if abspath.endswith('.json'):
        json.dump(data, f, sort_keys=True, indent=True)
    else:
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        f.write(data)
    f.close()

def export_assertions(project, jinja_env, base_dest_dir):
    dest_dir = os.path.join(base_dest_dir, 'assertions')
    template = jinja_env.get_template('assertion.html')
    os.mkdir(dest_dir)
    for assn in project.assertions:
        write_data(assn.json, dest_dir, '%s.json' % assn.basename)
        evidence_html = template.render(**assn.context)
        write_data(evidence_html, dest_dir, '%s.html' % assn.basename)

def export_badge_classes(project, jinja_env, base_dest_dir):
    dest_dir = os.path.join(base_dest_dir, 'badges')
    template = jinja_env.get_template('badge.html')
    os.mkdir(dest_dir)
    for badge in project.badges:
        if 'image' in badge.json:
            shutil.copy(badge.img_filename, dest_dir)
        write_data(badge.json, dest_dir, '%s.json' % badge.basename)
        criteria_html = template.render(**badge.context)
        write_data(criteria_html, dest_dir, '%s.html' % badge.basename)

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

    log("Exporting badge classes.")
    export_badge_classes(project, env, dest_dir)

    log("Exporting assertions.")
    export_assertions(project, env, dest_dir)

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

    if not args.badge in project.badges:
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
