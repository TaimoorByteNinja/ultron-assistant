# 🔵 Ultron — a JARVIS-style personal assistant

A glowing energy orb that **reacts to your hand** (webcam), **listens** to you and
**talks back** (voice), and — once set up — **controls your Android phone**.

Everything runs **locally** on your machine. The web UI is plain HTML/JS, and a tiny
Python server (standard library only) drives your phone over `adb`.

> ℹ️ This is a brand-new project, **separate** from the `modelscope/ultron`
> memory-server repo that happens to share the name.

---

## ✨ Features

- 🔵 **Reactive energy orb** — a particle orb that follows your hand's position and
  reacts when you open/close it, tracked live from your webcam.
- 🎤 **Voice commands** — talk to it: *“hello”*, *“what time is it”*, *“what day is it”*,
  *“your name”*, *“thank you”*.
- 🔊 **Speaks back** — replies are spoken out loud.
- 📱 **Phone control (optional)** — *“open YouTube on my phone”*,
  *“search lofi on YouTube”*, *“how many devices are connected”*, and more.

---

## 🧰 Tech stack

| Layer | What it uses |
|-------|--------------|
| Hand tracking | [MediaPipe Tasks Vision](https://developers.google.com/mediapipe) `hand_landmarker` (loaded from CDN) |
| Voice | Web Speech API — `SpeechRecognition` (in) + `speechSynthesis` (out) |
| Visuals | Canvas particle orb, vanilla JS — no framework |
| Server | Python 3 standard library (`http.server`) |
| Phone control | Android Debug Bridge (`adb`) |

No build step, no `npm install` — it's static files plus one Python script.

---

## 🚀 Quick start

```bash
cd ultron-assistant
./start.sh            # or:  python3 server.py   then open http://localhost:8000
```

1. Chrome opens `http://localhost:8000`.
2. Click **Activate**.
3. **Allow** the camera + microphone prompts.
4. Press **F11** for full-screen.
5. Say **“hello”**, **“what time is it”**, or wave your hand in front of the camera.

> **Use Google Chrome** — voice recognition needs it.
> An internet connection is required the first time (it downloads the hand-tracking model
> and MediaPipe runtime from a CDN).

---

## 📱 Phone control (optional)

Say things like *“open YouTube on my phone”* or *“search cat videos on YouTube”*.
To enable it you need `adb` and an Android phone with USB debugging on:

```bash
# 1) Install adb (one-time)
sudo apt install adb                 # Debian/Ubuntu
# macOS:   brew install android-platform-tools

# 2) On the phone: Settings → About phone → tap "Build number" 7×
#    → Developer options → enable "USB debugging"

# 3) Plug the phone in via USB, tap "Allow USB debugging" on the phone, then:
adb devices                          # your phone should be listed as "device"
```

Restart the server and the *“open …”* commands will drive the phone.

**Supported phone commands**

- `open <app> on my phone` — YouTube, WhatsApp, Chrome, Camera, Settings, Maps, Gmail, Instagram
- `search/play <query> on YouTube` — opens YouTube search results for the query
- `how many devices are connected?`
- `wake / unlock my phone`

The spoken-name → package-name map lives in `server.py` (`APP_PACKAGES`) — extend it freely.

> **Note:** `adb` is **not** bundled in this repo. Install it via your package manager
> (above). The server automatically uses a local `platform-tools/adb` if you drop one in,
> otherwise it falls back to `adb` on your `PATH`.

---

## 📂 Project structure

| File | Purpose |
|------|---------|
| `index.html` | The entire UI: particle orb, hand tracking, voice recognition/synthesis. |
| `server.py`  | Local web server + `POST /api/command` endpoint for phone control via `adb`. |
| `start.sh`   | Convenience launcher — starts the server and opens it in Chrome. |

---

## 🗺️ Roadmap

- **Phase 1 (done)** — reactive orb, voice commands, spoken replies.
- **Phase 2 (in progress)** — richer phone control over `adb`.
- **Ideas** — more built-in intents, smart-home hooks, offline speech.

---

## 🔒 Privacy

The camera feed and microphone audio are processed **in your browser** — nothing is
uploaded. The only outbound requests are the one-time CDN downloads of the MediaPipe
runtime and hand-tracking model. Phone commands run locally through `adb`.

---

## 📄 License

Released under the [MIT License](LICENSE).
