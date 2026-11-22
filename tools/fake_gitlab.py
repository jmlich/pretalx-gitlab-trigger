"""Fake GitLab trigger endpoint for manual tests. It prints every request it gets.

Run it next to pretalx and set the plugin URL to http://127.0.0.1:9999/trigger.
"""

import datetime as dt
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(dt.datetime.now().isoformat(timespec="seconds"), self.command, self.path, flush=True)  # noqa: T201, DTZ005
        self.send_response(201)
        self.end_headers()


HTTPServer(("127.0.0.1", 9999), Handler).serve_forever()
