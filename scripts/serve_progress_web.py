"""Serve progress files on your home LAN. Optional: tunnel to Internet.

LAN only (same WiFi):
  python serve_progress_web.py
  Phone browser: http://YOUR-PC-IP:8765/

Internet via Cloudflare Tunnel (no router port forwarding):
  1. winget install Cloudflare.cloudflared
  2. python serve_progress_web.py          (leave running)
  3. In another terminal:
     cloudflared tunnel --url http://127.0.0.1:8765
  4. Copy the https://....trycloudflare.com URL to your phone

See WEB_PUBLISH.txt for OneDrive public share (easiest, no server).
"""
from __future__ import annotations

import http.server
import os
import socket
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PORT = 8765

_FILES = {
    '/': 'status.html',
    '/status.html': 'status.html',
    '/STATUS.txt': 'STATUS.txt',
    '/SYNC_STAMP.txt': 'SYNC_STAMP.txt',
    '/PROGRESS.rss': 'PROGRESS.rss',
}


class ProgressHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=_ROOT, **kwargs)

    def do_GET(self) -> None:
        path = self.path.split('?', 1)[0]
        if path in _FILES:
            self.path = '/' + _FILES[path]
        return super().do_GET()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f'{self.address_string()} {fmt % args}\n')


def _lan_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return '127.0.0.1'


def main() -> int:
    os.chdir(_ROOT)
    ip = _lan_ip()
    server = http.server.ThreadingHTTPServer(('0.0.0.0', _PORT), ProgressHandler)
    print(f'Serving progress from {_ROOT}')
    print(f'LAN:    http://{ip}:{_PORT}/')
    print(f'Local:  http://127.0.0.1:{_PORT}/')
    print('Internet: see WEB_PUBLISH.txt (Cloudflare tunnel or OneDrive share)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopped.')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())