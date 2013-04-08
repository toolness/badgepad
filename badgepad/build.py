import os
import shutil
import json

import jinja2

from . import pkg_path

def write_data(data, *filename):
    abspath = os.path.join(*filename)
    dirname = os.path.dirname(abspath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    f = open(abspath, 'w')
    if abspath.endswith('.json'):
        json.dump(data, f, sort_keys=True, indent=True)
    else:
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        f.write(data)
    f.close()

def export_assertions(project, jinja_env, base_dest_dir):
    template = jinja_env.get_template('assertion.html')
    for assn in project.assertions:
        write_data(assn.json, base_dest_dir, *assn.paths['json'])
        evidence_html = template.render(assertion=assn)
        write_data(evidence_html, base_dest_dir, *assn.paths['html'])

def export_badge_classes(project, jinja_env, base_dest_dir):
    template = jinja_env.get_template('badge.html')
    for badge in project.badges:
        write_data(badge.json, base_dest_dir, *badge.paths['json'])
        criteria_html = template.render(badge=badge)
        write_data(criteria_html, base_dest_dir, *badge.paths['html'])
        if badge.image_url:
            shutil.copy(badge.image_filename,
                        os.path.join(base_dest_dir, *badge.paths['png']))

def build_website(project, dest_dir):
    loader = jinja2.FileSystemLoader([
        project.TEMPLATES_DIR,
        pkg_path('samples', 'templates')
    ])
    env = jinja2.Environment(loader=loader)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    if os.path.exists(project.STATIC_DIR):
        shutil.copytree(project.STATIC_DIR, dest_dir)
    write_data(project.config['issuer'], dest_dir, *project.paths['json'])
    export_badge_classes(project, env, dest_dir)
    export_assertions(project, env, dest_dir)
