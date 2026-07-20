#!/usr/bin/env bash
# Ultron launcher: starts the local server and opens it in Google Chrome.
cd "$(dirname "$0")" || exit 1

# Start the server (background) if it isn't already running.
if ! curl -s -o /dev/null "http://localhost:8000/"; then
  python3 server.py &
  SRV=$!
  sleep 1.5
fi

# Open in Chrome.
URL="http://localhost:8000/"
if command -v google-chrome >/dev/null; then
  google-chrome --new-window "$URL" >/dev/null 2>&1 &
elif command -v google-chrome-stable >/dev/null; then
  google-chrome-stable --new-window "$URL" >/dev/null 2>&1 &
else
  echo "Open this in Chrome:  $URL"
fi

echo "Ultron is running at $URL   (press Ctrl+C to stop the server)"
wait ${SRV:-}
