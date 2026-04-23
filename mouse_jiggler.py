"""
Mouse Jiggler - a small Windows utility that nudges the mouse cursor periodically
to prevent the system from going idle.

Features:
 - Adjustable interval (how often to jiggle)
 - Adjustable movement distance (how far to move)
 - Selectable mode: "Jiggle" (move then move back) or "Circle" (small circular motion)
 - Start / Stop button
 - Runs using the Win32 API (ctypes) so no third-party libraries are required.
"""

import ctypes
import math
import threading
import time
import tkinter as tk
from tkinter import ttk


# ---------------- Low-level mouse helpers ---------------- #

user32 = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def set_cursor_pos(x, y):
    user32.SetCursorPos(int(x), int(y))


# ---------------- Jiggler worker ---------------- #

class Jiggler:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()

        # User-adjustable parameters (updated live from the GUI)
        self.interval = 5.0   # seconds between movements
        self.distance = 20    # pixels to move
        self.mode = "Jiggle"  # "Jiggle" or "Circle"

    # --- thread control ---
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    # --- main loop ---
    def _run(self):
        while not self._stop_event.is_set():
            try:
                if self.mode == "Circle":
                    self._do_circle()
                else:
                    self._do_jiggle()
            except Exception:
                pass

            # Sleep in small increments so Stop reacts quickly.
            end = time.time() + max(0.1, float(self.interval))
            while time.time() < end:
                if self._stop_event.is_set():
                    return
                time.sleep(0.05)

    def _do_jiggle(self):
        x, y = get_cursor_pos()
        d = int(self.distance)
        set_cursor_pos(x + d, y)
        time.sleep(0.05)
        set_cursor_pos(x, y)

    def _do_circle(self):
        x, y = get_cursor_pos()
        r = max(1, int(self.distance))
        steps = 24
        for i in range(steps + 1):
            if self._stop_event.is_set():
                break
            angle = (2 * math.pi) * (i / steps)
            nx = x + int(r * math.cos(angle)) - r  # start/end at original x
            ny = y + int(r * math.sin(angle))
            set_cursor_pos(nx, ny)
            time.sleep(0.01)
        set_cursor_pos(x, y)


# ---------------- GUI ---------------- #

class JigglerApp:
    def __init__(self, root):
        self.root = root
        self.jiggler = Jiggler()

        root.title("Mouse Jiggler")
        root.resizable(False, False)
        try:
            root.iconbitmap(default="")  # no custom icon
        except Exception:
            pass

        pad = {"padx": 10, "pady": 6}
        frm = ttk.Frame(root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        # --- Interval ---
        ttk.Label(frm, text="Interval (seconds):").grid(row=0, column=0, sticky="w", **pad)
        self.interval_var = tk.DoubleVar(value=5.0)
        self.interval_scale = ttk.Scale(
            frm, from_=0.5, to=120, orient="horizontal",
            variable=self.interval_var, length=220,
            command=lambda _=None: self._sync_labels()
        )
        self.interval_scale.grid(row=0, column=1, sticky="we", **pad)
        self.interval_lbl = ttk.Label(frm, text="5.0 s", width=8)
        self.interval_lbl.grid(row=0, column=2, sticky="w", **pad)

        # --- Distance ---
        ttk.Label(frm, text="Movement (pixels):").grid(row=1, column=0, sticky="w", **pad)
        self.distance_var = tk.IntVar(value=20)
        self.distance_scale = ttk.Scale(
            frm, from_=1, to=300, orient="horizontal",
            variable=self.distance_var, length=220,
            command=lambda _=None: self._sync_labels()
        )
        self.distance_scale.grid(row=1, column=1, sticky="we", **pad)
        self.distance_lbl = ttk.Label(frm, text="20 px", width=8)
        self.distance_lbl.grid(row=1, column=2, sticky="w", **pad)

        # --- Mode ---
        ttk.Label(frm, text="Mode:").grid(row=2, column=0, sticky="w", **pad)
        self.mode_var = tk.StringVar(value="Jiggle")
        mode_frame = ttk.Frame(frm)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(mode_frame, text="Jiggle", variable=self.mode_var, value="Jiggle").pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_frame, text="Circle", variable=self.mode_var, value="Circle").pack(side="left")

        # --- Start / Stop button ---
        self.toggle_btn = ttk.Button(frm, text="Start", command=self.toggle)
        self.toggle_btn.grid(row=3, column=0, columnspan=3, sticky="we", **pad)

        # --- Status ---
        self.status_var = tk.StringVar(value="Stopped")
        self.status_lbl = ttk.Label(frm, textvariable=self.status_var, foreground="#b00")
        self.status_lbl.grid(row=4, column=0, columnspan=3, **pad)

        # Keep jiggler parameters in sync
        self._sync_labels()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Periodically push current values to the jiggler
        self._tick()

    def _sync_labels(self):
        self.interval_lbl.config(text=f"{self.interval_var.get():.1f} s")
        self.distance_lbl.config(text=f"{int(self.distance_var.get())} px")

    def _tick(self):
        # Push live values to the worker.
        self.jiggler.interval = float(self.interval_var.get())
        self.jiggler.distance = int(self.distance_var.get())
        self.jiggler.mode = self.mode_var.get()
        self.root.after(200, self._tick)

    def toggle(self):
        if self.jiggler.is_running():
            self.jiggler.stop()
            self.toggle_btn.config(text="Start")
            self.status_var.set("Stopped")
            self.status_lbl.config(foreground="#b00")
        else:
            self.jiggler.start()
            self.toggle_btn.config(text="Stop")
            self.status_var.set("Running")
            self.status_lbl.config(foreground="#080")

    def _on_close(self):
        self.jiggler.stop()
        self.root.after(100, self.root.destroy)


def main():
    root = tk.Tk()
    try:
        # Use a modern ttk theme on Windows
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    JigglerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
