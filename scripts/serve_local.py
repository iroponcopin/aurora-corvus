#!/usr/bin/env python3
"""Tiny static server for previewing the built site locally.

Not part of the build. It exists because `python3 -m http.server` evaluates
os.getcwd() at import time, which this sandbox refuses -- so the root is
passed in explicitly and getcwd() is never called.
"""
import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

handler = functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT))
print(f"serving {ROOT} on http://127.0.0.1:{PORT}/", flush=True)
ThreadingHTTPServer(("127.0.0.1", PORT), handler).serve_forever()
