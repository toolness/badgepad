import os
import sys
import hashlib
import threading
import time
import shutil
import tempfile
import traceback
import SimpleHTTPServer
import SocketServer

from .build import build_website
from .project import Project

def get_dir_state(dirname):
    state = []
    for dirpath, dirnames, filenames in os.walk(dirname):
        dirnames[:] = [dirname for dirname in dirnames if dirname[0] != '.']
        for filename in filenames:
            if filename[0] == '.': continue
            fullpath = os.path.join(dirpath, filename)
            state.extend([filename, str(int(os.stat(fullpath).st_mtime))])
    return hashlib.md5(':'.join(state)).hexdigest()

def start_file_server(ip, port):
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer((ip, port), handler)
    print "serving at port %s on %s" % (port, ip)
    httpd.serve_forever()

def auto_rebuilder(root_dir, dest_dir):
    laststate = None
    while True:
        currstate = get_dir_state(root_dir)
        if currstate != laststate:
            laststate = currstate
            sys.stdout.write("rebuilding website... ")
            sys.stdout.flush()
            try:
                build_website(Project(root_dir), dest_dir=dest_dir)
                sys.stdout.write("done.\n")
            except Exception:
                traceback.print_exc(file=sys.stdout)
        yield

def start_auto_rebuild_server(root_dir, ip, port):
    dest_dir = tempfile.mkdtemp()
    thread = threading.Thread(target=start_file_server,
                              kwargs=dict(ip=ip, port=port))
    thread.daemon = True
    thread.start()
    try:
        for _ in auto_rebuilder(root_dir, dest_dir):
            os.chdir(dest_dir)
            time.sleep(1)
    finally:
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
