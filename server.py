#!/usr/bin/env python3
"""Ultron assistant — local server.

Serves the web UI on http://localhost:8000 (localhost is a "secure context",
so the browser allows camera, microphone and speech recognition).

Also exposes POST /api/command, which the browser calls for phone control.
Phase 1: adb may be missing / no phone -> returns a friendly message.
Phase 2: install adb + plug in an Android phone with USB debugging -> it works.
"""
import json
import re
import shutil
import socket
import subprocess
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
PORT = 8000


def adb_exe():
    """Locate adb: prefer the bundled platform-tools, fall back to PATH."""
    local = ROOT / "platform-tools" / "adb"
    if local.exists():
        return str(local)
    return shutil.which("adb")

# Spoken phrase -> Android app package name (extend freely).
APP_PACKAGES = {
    "youtube":  "com.google.android.youtube",
    "whatsapp": "com.whatsapp",
    "chrome":   "com.android.chrome",
    "camera":   "com.android.camera",
    "settings": "com.android.settings",
    "maps":     "com.google.android.apps.maps",
    "gmail":    "com.google.android.gm",
    "instagram":"com.instagram.android",
}


def adb(*args, timeout=15):
    """Run an adb command; return (ok, stdout/err)."""
    exe = adb_exe()
    if not exe:
        return False, "adb-missing"
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def phone_connected():
    ok, out = adb("devices")
    if not ok:
        return False
    lines = [l for l in out.splitlines()[1:] if l.strip() and "device" in l.split()[-1:]]
    return len(lines) > 0


def device_list():
    """Serials of connected, authorized devices."""
    ok, out = adb("devices")
    if not ok:
        return []
    devs = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devs.append(parts[0])
    return devs


def youtube_search(query: str) -> bool:
    """Open YouTube search results for `query` on the phone (URL-encoded, so spaces are safe)."""
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    ok, _ = adb("shell", "am", "start", "-a", "android.intent.action.VIEW",
                "-d", url, "-p", "com.google.android.youtube")
    if not ok:  # YouTube app refused -> let the phone pick a handler
        ok, _ = adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url)
    return ok


def extract_youtube_query(text: str):
    """Pull the phrase out of 'search cat videos on youtube', 'play lofi on youtube', etc."""
    for pat in (
        r'(?:search|play|find|look up)\s+(?:for\s+)?(.+?)\s+(?:on|in|from)\s+(?:the\s+)?youtube',
        r'search\s+youtube\s+(?:for\s+)?(.+)',
        r'youtube\s+(?:search|play|for)\s+(.+)',
        r'(?:search|play|find)\s+(?:for\s+)?(.+?)\s+youtube',
    ):
        m = re.search(pat, text)
        if m:
            q = re.sub(r'\bon (my|the)\s+phone\b', '', m.group(1)).strip()
            if q:
                return q
    return None


def run_command(text: str) -> dict:
    """Interpret a spoken command and act on the phone via adb."""
    if adb_exe() is None:
        return {"ok": False,
                "message": "Phone control needs A D B installed. Run: sudo apt install adb."}

    # "how many devices/phones are connected?"
    if ("how many" in text and ("device" in text or "phone" in text)) or "devices connected" in text:
        n = len(device_list())
        if n == 0:
            return {"ok": True, "message": "No devices are connected right now."}
        return {"ok": True, "message": f"You have {n} device{'' if n == 1 else 's'} connected."}

    if not phone_connected():
        return {"ok": False,
                "message": "No phone is connected. Plug in your Android phone and enable U S B debugging."}

    # Always wake + dismiss the simple keyguard first so the launched app is visible.
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    adb("shell", "input", "keyevent", "82")  # dismiss swipe-only keyguard

    # Search / play on YouTube: "search cat videos on youtube", "play lofi on youtube".
    if "youtube" in text and any(w in text for w in ("search", "play", "find", "look up")):
        q = extract_youtube_query(text)
        if q:
            if youtube_search(q):
                return {"ok": True, "message": f"Searching YouTube for {q} on your phone."}
            return {"ok": False, "message": f"I could not search YouTube for {q}."}

    # Open a named app (checked BEFORE the generic "wake phone", so
    # "open youtube on my phone" opens YouTube instead of just waking).
    for name, pkg in APP_PACKAGES.items():
        if name in text:
            ok, _ = adb("shell", "monkey", "-p", pkg,
                        "-c", "android.intent.category.LAUNCHER", "1")
            if ok:
                return {"ok": True, "message": f"Opening {name} on your phone."}
            return {"ok": False, "message": f"Could not open {name}. Is it installed?"}

    # No specific app named -> it was just a "wake/open my phone" request.
    if "phone" in text and ("open" in text or "wake" in text or "unlock" in text):
        return {"ok": True, "message": "Your phone is awake."}

    return {"ok": False, "message": "I heard a phone command but did not recognise the app."}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):  # quieter console
        pass

    def end_headers(self):      # never serve a stale cached page
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        if self.path.rstrip("/") == "/api/command":
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:  # noqa: BLE001
                body = {}
            result = run_command(str(body.get("text", "")).lower())
            payload = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_error(404)


class DualStackServer(ThreadingHTTPServer):
    """Serve on both IPv4 (127.0.0.1) and IPv6 (::1) so 'localhost' always works."""
    address_family = socket.AF_INET6

    def server_bind(self):
        # Accept IPv4-mapped addresses too (dual stack).
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()


if __name__ == "__main__":
    print(f"Ultron running →  http://localhost:{PORT}")
    print("Open that in Google Chrome, then click Activate.  Ctrl+C to stop.")
    DualStackServer(("::", PORT), Handler).serve_forever()
