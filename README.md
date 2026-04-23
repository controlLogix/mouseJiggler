# Mouse Jiggler

A tiny Windows utility that nudges your mouse cursor on a timer so your
computer never thinks you're idle. Single-file Python app with a small
Tk GUI — no third-party runtime dependencies.

![platform](https://img.shields.io/badge/platform-Windows-blue)
![python](https://img.shields.io/badge/python-3.10%2B-green)

## Features

- **Adjustable interval** — 0.5 to 120 seconds between movements
- **Adjustable movement length** — 1 to 300 pixels
- **Two modes**
  - `Jiggle` — quick right/left nudge
  - `Circle` — small circular sweep back to the start position
- **Start / Stop** toggle with live status indicator
- Uses only the Windows API via `ctypes` + `tkinter` (stdlib only)

## Run from source

```powershell
python mouse_jiggler.py
```

Requires Python 3.10+ on Windows. No `pip install` needed.

## Build a standalone `.exe`

```powershell
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name MouseJiggler mouse_jiggler.py
```

The resulting `MouseJiggler.exe` appears in `dist/`. It's a single
portable file (~10 MB) — no installer, no Python required on the
target machine.

## How it works

Every *interval* seconds the app calls `SetCursorPos` via `user32.dll`
to move the cursor a small amount and then return it to the original
position. That single "real" mouse movement is enough to reset
Windows' idle / screensaver / away-from-keyboard timers without
actually disrupting what you're doing.

## Files

| File | Purpose |
| --- | --- |
| `mouse_jiggler.py` | Source (GUI + jiggler thread) |
| `MouseJiggler.exe` | Pre-built standalone executable |

## License

MIT
