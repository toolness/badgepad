import os
import hashlib
import threading
import time
import shutil
import tempfile
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

def start_auto_rebuild_server(root_dir, ip, port):
    dirname = tempfile.mkdtemp()
    thread = threading.Thread(target=start_file_server,
                              kwargs=dict(ip=ip, port=port))
    thread.daemon = True
    thread.start()
    laststate = None
    try:
        while True:
            currstate = get_dir_state(root_dir)
            if currstate != laststate:
                laststate = currstate
                project = Project(root_dir)
                print "rebuilding website... ",
                build_website(project, dest_dir=dirname)
                print "done."
                os.chdir(dirname)
            time.sleep(1)
    finally:
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
