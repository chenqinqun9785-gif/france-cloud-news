import http.server
import socketserver
import sys
import os

PORT = int(os.environ.get("PORT", 8081))
DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving {DIR} on http://localhost:{PORT}")
    httpd.serve_forever()
