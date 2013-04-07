import os
import sys
import shutil
import argparse

from .project import Project
from .build import build_website
from .server import start_auto_rebuild_server

def require_project(fn):
    def wrapper(project, args):
        if not project.exists('config.yml'):
            log('This directory does not appear to contain a project.')
            sys.exit(1)
        fn(project, args)
    wrapper.__doc__ = fn.__doc__
    return wrapper

def log(text):
    sys.stdout.write(text + '\n')

def pkg_path(*args):
    return os.path.join(PKG_ROOT, *args)

PKG_ROOT = os.path.dirname(os.path.abspath(__file__))

@require_project
def cmd_serve(project, args):
    """
    Serve website.
    """

    start_auto_rebuild_server(project.ROOT, ip=args.ip, port=args.port)

@require_project
def cmd_build(project, args):
    """
    Build website.
    """

    if args.base_url:
        project.set_base_url(args.base_url)

    build_website(project, dest_dir=project.path('dist'))
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

@require_project
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

@require_project
def cmd_issue(project, args):
    """
    Issue a badge to a recipient.
    """

    basename = '%s.%s' % (args.recipient, args.badge)
    filename = project.path('assertions', '%s.yml' % basename)

    if not args.badge in project.badges:
        log("The badge '%s' does not exist." % args.badge)
        sys.exit(1)

    if args.recipient not in project.recipients:
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

    serve = subparsers.add_parser('serve', help=cmd_serve.__doc__)
    serve.add_argument('-i', '--ip', help='ip address',
                       default='127.0.0.1')
    serve.add_argument('-p', '--port', help='port', type=int, default=8000)
    serve.set_defaults(func=cmd_serve)

    build = subparsers.add_parser('build', help=cmd_build.__doc__)
    build.add_argument('-u', '--base-url', help='alternate base URL')
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
