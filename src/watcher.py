import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess


class ReloadHandler(FileSystemEventHandler):
    def __init__(self, server_process):
        self.server_process = server_process

    def on_modified(self, event):
        path: str = str(event.src_path)
        if path.startswith('./static') and path.endswith('.html'):
            return

        any_file_changed = (path.endswith('.py') or path.endswith('.html') or path.endswith('.css') or
                            path.endswith('.js') or path.endswith('.json'))

        if any_file_changed:
            print(80*'~')
            print(path)
            print(80*'~')
            print("Changes detected, restarting server...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = subprocess.Popen(
                [sys.executable, 'server.py'])


if __name__ == "__main__":
    server_address = ('', 8000)
    handler = SimpleHTTPRequestHandler
    server = HTTPServer(server_address, handler)

    server_process = subprocess.Popen([sys.executable, 'server.py'])
    observer = Observer()
    observer.schedule(ReloadHandler(server_process), path='.', recursive=True)
    observer.start()

    try:
        print("Serving on http://localhost:8000")
        server.serve_forever()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
