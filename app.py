"""
Azzahra Service Information Board — Kiosk Mode + Auto Pagination
================================================================
Light theme optimised for daylight visibility on slow hardware.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
import sys
import os

_requests = None

def _get_requests():
    global _requests
    if _requests is None:
        import requests as _req
        _requests = _req
    return _requests

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
API_URL       = "http://azzahracomputertegal.com/apipy/api.php"
REFRESH_SEC   = 30
PAGE_FLIP_SEC = 8
TOAST_MS      = 4000
RFID_TIMEOUT  = 500

# ═══════════════════════════════════════════════════════════
#  PALETTE  —  Light / Daylight-optimised
# ═══════════════════════════════════════════════════════════
BG           = "#f5f7fa"
HEADER_BG    = "#e4e8ee"
ROW_ALT      = "#edf0f4"
GRID         = "#cdd4dc"
GRID_MED     = "#b4bcc6"
AMBER        = "#d49500"
AMBER_DIM    = "#a87800"
TEXT         = "#3d4f5f"
TEXT_BRIGHT  = "#1a2533"
TEXT_DIM     = "#8896a6"
GREEN        = "#00884a"
GREEN_BG     = "#daf5e6"
GREEN_BD     = "#6fcf97"
ORANGE       = "#d97706"
ORANGE_BG    = "#fef3dc"
ORANGE_BD    = "#f5c563"
RED          = "#c62828"
BLUE_SOFT    = "#2563eb"
PURPLE_SOFT  = "#6d5fcb"

ROW_H  = 48
HDR_H  = 52
PAD    = 18

COLS = [
    ("NO",        80),
    ("CUSTOMER", 280),
    ("KELUHAN",    0),
    ("STATUS",   180),
    ("WAIT",     120),
]


# ═══════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ═══════════════════════════════════════════════════════════
class SplashScreen:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w, h = 420, 180
        self.splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.splash.configure(bg=HEADER_BG)

        outer = tk.Frame(self.splash, bg=AMBER, padx=2, pady=2)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=HEADER_BG)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="AZZAHRA", font=("Consolas", 32, "bold"),
                 bg=HEADER_BG, fg=AMBER).pack(pady=(24, 0))
        tk.Label(inner, text="SERVICE TASK  —  LOADING…",
                 font=("Consolas", 11), bg=HEADER_BG, fg=TEXT_DIM).pack()

        self._bar_frame = tk.Frame(inner, bg=GRID_MED, height=4)
        self._bar_frame.pack(fill="x", padx=24, pady=14)
        self._bar = tk.Frame(self._bar_frame, bg=AMBER, height=4, width=0)
        self._bar.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        self._progress = 0.0
        self._animate()
        self.splash.lift()
        self.splash.update()

    def _animate(self):
        if self._progress < 0.9:
            self._progress = min(self._progress + 0.04, 0.9)
            self._bar.place(relwidth=self._progress)
            self.splash.after(60, self._animate)

    def finish(self):
        self._bar.place(relwidth=1.0)
        self.splash.after(300, self.splash.destroy)


# ═══════════════════════════════════════════════════════════
#  TOAST
# ═══════════════════════════════════════════════════════════
class Toast:
    def __init__(self, parent, message, accent=GREEN):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="#ffffff",
                              highlightbackground=GRID_MED,
                              highlightthickness=1)
        self.frame.place(relx=1.0, rely=0.0, anchor="ne", x=-14, y=14)

        tk.Frame(self.frame, bg=accent, width=4).place(
            x=0, y=0, relheight=1.0, anchor="nw")

        tk.Label(self.frame, text=f"  {message}",
                 font=("Consolas", 12, "bold"),
                 bg="#ffffff", fg=TEXT_BRIGHT,
                 padx=14, pady=11, anchor="w").pack(fill="x")

        self.bar = tk.Frame(self.frame, bg=accent, height=2)
        self.bar.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        self._shrink(TOAST_MS)
        parent.after(TOAST_MS, self._destroy)

    def _shrink(self, left):
        if left <= 0:
            return
        try:
            self.bar.place(relx=0, rely=1.0,
                           relwidth=max(left / TOAST_MS, 0), anchor="sw")
            self.parent.after(40, self._shrink, left - 40)
        except tk.TclError:
            pass

    def _destroy(self):
        try:
            self.frame.destroy()
        except tk.TclError:
            pass


# ═══════════════════════════════════════════════════════════
#  COLUMN HELPER
# ═══════════════════════════════════════════════════════════
def calc_cols(total_w):
    xs, ws = [], []
    x, fill_i = 0, None
    for i, (_, w) in enumerate(COLS):
        xs.append(x)
        if w == 0:
            fill_i = i
            ws.append(0)
        else:
            ws.append(w)
        x += w
    if fill_i is not None:
        ws[fill_i] = max(total_w - sum(w for _, w in COLS if w > 0), 80)
        x = 0
        for i in range(len(COLS)):
            xs[i] = x
            x += ws[i]
    return xs, ws


# ═══════════════════════════════════════════════════════════
#  BOARD CANVAS
# ═══════════════════════════════════════════════════════════
class BoardCanvas(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, **kw)
        self.full_orders = []
        self.pages = [[]]
        self.current_page = 0
        self.max_rows = 10
        self.cx = []
        self.cw = []

    def set_data(self, orders):
        self.full_orders = orders
        self.current_page = 0
        self._paginate()

    def update_cols(self, cx, cw):
        self.cx, self.cw = cx, cw

    def _paginate(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 80 or h < 80 or not self.cx:
            return
        self.max_rows = max(1, h // ROW_H)
        self.pages = [
            self.full_orders[i:i + self.max_rows]
            for i in range(0, len(self.full_orders), self.max_rows)
        ]
        if not self.pages:
            self.pages = [[]]
        if self.current_page >= len(self.pages):
            self.current_page = 0
        self._draw()

    def next_page(self):
        if len(self.pages) <= 1:
            return False
        self.current_page = (self.current_page + 1) % len(self.pages)
        self._draw()
        return True

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        if w < 80 or not self.cx:
            return
        page_data = (self.pages[self.current_page]
                     if self.current_page < len(self.pages) else [])
        if not page_data:
            self.create_text(w // 2, 100,
                             text="— Loading... —",
                             font=("Consolas", 20, "bold"),
                             fill=TEXT_DIM, anchor="center")
            return
        for i, o in enumerate(page_data):
            self._row(i * ROW_H, o, i)

    def _row(self, y, o, idx):
        w = self.winfo_width()
        if idx % 2 == 1:
            self.create_rectangle(0, y, w, y + ROW_H, fill=ROW_ALT, outline="")
        self.create_line(0, y + ROW_H, w, y + ROW_H, fill=GRID)
        for xi in self.cx[1:-1]:
            self.create_line(xi, y, xi, y + ROW_H, fill=GRID)

        cy = y + ROW_H // 2

        xi, cw = self.cx[0], self.cw[0]
        self.create_text(xi + cw // 2, cy, text=f"{idx + 1:02d}",
                         font=("Consolas", 13), fill=TEXT_DIM, anchor="center")

        xi, cw = self.cx[1], self.cw[1]
        nama = self._fit(o.get("nama_customer", "-"), cw, 13)
        self.create_text(xi + PAD, cy, text=nama,
                         font=("Consolas", 13, "bold"), fill=TEXT_BRIGHT, anchor="w")

        xi, cw = self.cx[2], self.cw[2]
        raw_keluhan = o.get("keluhan", "-").replace("\n", ", ").replace("\r", "")
        kel = self._fit(raw_keluhan, cw, 11)
        self.create_text(xi + PAD, cy, text=kel,
                         font=("Consolas", 11), fill=TEXT, anchor="w")

        xi, cw = self.cx[3], self.cw[3]
        st = o.get("status_order", "")
        if "Baru" in st:
            bg, fg, bd, lbl = GREEN_BG, GREEN, GREEN_BD, "● BARU"
        else:
            bg, fg, bd, lbl = ORANGE_BG, ORANGE, ORANGE_BD, "● DIPROSES"
        bx, by, bw, bh = xi + 10, y + 10, cw - 20, ROW_H - 20
        self.create_rectangle(bx, by, bx + bw, by + bh, fill=bg, outline=bd)
        self.create_text(bx + bw // 2, by + bh // 2, text=lbl,
                         font=("Consolas", 11, "bold"), fill=fg, anchor="center")

        xi, cw = self.cx[4], self.cw[4]
        hari = int(o.get("hari_menunggu", 0))
        if hari == 0:
            txt, fg = "TODAY", AMBER
        elif hari == 1:
            txt, fg = "1 HARI", TEXT
        else:
            txt = f"{hari} HARI"
            fg = RED if hari > 7 else (ORANGE if hari > 3 else TEXT)
        self.create_text(xi + cw - PAD, cy, text=txt,
                         font=("Consolas", 12, "bold"), fill=fg, anchor="e")

    @staticmethod
    def _fit(text, col_w, fsize):
        ch = int((col_w - PAD * 2) / (fsize * 0.62))
        return text if len(text) <= ch else text[:max(ch - 2, 1)] + ".."


# ═══════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════
class AzzahraBoard:

    def __init__(self, root: tk.Tk, splash: SplashScreen):
        self.root = root
        self.splash = splash
        self.root.title("Azzahra Service Task")
        self.root.configure(bg=BG)

        self.cx, self.cw = calc_cols(1200)
        self._rfid_timer = None
        self._page_flip_job = None
        self._data_refresh_job = None
        self._resize_job = None

        self._style_scrollbar()
        self._build_title()
        self._build_headers()
        self._build_data()
        self._build_hidden_rfid()

        self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)
        self.root.update_idletasks()

        self.splash.finish()
        self._tick_clock()
        self.root.after(200, self._load_orders)

    # ──────────────────────────────────────────────────────
    def _style_scrollbar(self):
        s = ttk.Style()
        s.theme_use("clam")

    def _build_title(self):
        bar = tk.Frame(self.root, bg=HEADER_BG, height=62)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self.dot = tk.Canvas(bar, width=12, height=12,
                             bg=HEADER_BG, highlightthickness=0)
        self.dot.pack(side="left", padx=(24, 8), pady=25)
        self.dot.create_oval(1, 1, 11, 11, fill=GREEN, outline="")

        tk.Label(bar, text="AZZAHRA", font=("Consolas", 24, "bold"),
                 bg=HEADER_BG, fg=AMBER).pack(side="left")
        tk.Label(bar, text="  SERVICE  TASK",
                 font=("Consolas", 13),
                 bg=HEADER_BG, fg=AMBER_DIM).pack(side="left")

        rf = tk.Frame(bar, bg=HEADER_BG)
        rf.pack(side="right", padx=24)

        self.page_lbl = tk.Label(rf, text="", font=("Consolas", 11),
                                 bg=HEADER_BG, fg=AMBER_DIM)
        self.page_lbl.pack(side="right", padx=(18, 0))

        self.cnt_lbl = tk.Label(rf, text="", font=("Consolas", 11),
                                bg=HEADER_BG, fg=TEXT_DIM)
        self.cnt_lbl.pack(side="right", padx=(18, 0))

        self.clk_lbl = tk.Label(rf, text="", font=("Consolas", 14, "bold"),
                                bg=HEADER_BG, fg=AMBER)
        self.clk_lbl.pack(side="right")

        tk.Frame(self.root, bg=AMBER, height=2).pack(fill="x")

    def _build_headers(self):
        self.hdr = tk.Canvas(self.root, bg=HEADER_BG, height=HDR_H,
                             highlightthickness=0)
        self.hdr.pack(fill="x")
        tk.Frame(self.root, bg=GRID_MED, height=1).pack(fill="x")

    def _draw_headers(self):
        self.hdr.delete("all")
        if not self.cx:
            return
        w = self.hdr.winfo_width()
        if w < 80:
            return
        cy = HDR_H // 2
        for i, (name, _) in enumerate(COLS):
            xi = self.cx[i]
            self.hdr.create_text(xi + PAD, cy, text=name,
                                 font=("Consolas", 11, "bold"),
                                 fill=AMBER, anchor="w")
            if 0 < i < len(COLS) - 1:
                self.hdr.create_line(xi, 0, xi, HDR_H, fill=GRID)

    def _build_data(self):
        self.board = BoardCanvas(self.root)
        self.board.pack(fill="both", expand=True)
        self.board.bind("<Configure>", self._on_board_resize)

    def _on_board_resize(self, _e=None):
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(80, self._apply_resize)

    def _apply_resize(self):
        self._resize_job = None
        w = self.board.winfo_width()
        h = self.board.winfo_height()
        if w < 80 or h < 80:
            return
        self.cx, self.cw = calc_cols(w)
        self.board.update_cols(self.cx, self.cw)
        self._draw_headers()
        self.board._paginate()

    # ──────────────────────────────────────────────────────
    #  HIDDEN RFID
    # ──────────────────────────────────────────────────────
    def _build_hidden_rfid(self):
        self.rfid = tk.Entry(self.root, width=1,
                             bg=BG, fg=BG,
                             insertbackground=BG,
                             bd=0, highlightthickness=0,
                             relief="flat")
        self.rfid.place(x=-50, y=-50)
        self.rfid.bind("<Return>", self._rfid_enter)
        self.rfid.bind("<KeyRelease>", self._rfid_key)
        self.root.after(300, lambda: self.rfid.focus_set())

    def _rfid_enter(self, _e):
        if self._rfid_timer:
            self.root.after_cancel(self._rfid_timer)
            self._rfid_timer = None
        code = self.rfid.get().strip()
        self.rfid.delete(0, "end")
        if code:
            self._scan(code)

    def _rfid_key(self, e):
        if e.keysym == "Return":
            return
        if self._rfid_timer:
            self.root.after_cancel(self._rfid_timer)
        self._rfid_timer = self.root.after(RFID_TIMEOUT, self._rfid_timeout)

    def _rfid_timeout(self):
        self._rfid_timer = None
        code = self.rfid.get().strip()
        self.rfid.delete(0, "end")
        if code:
            self._scan(code)

    def _scan(self, nokartu):
        def _worker():
            try:
                req = _get_requests()
                r = req.post(f"{API_URL}?action=scan_rfid",
                             json={"nokartu": nokartu}, timeout=6)
                d = r.json()
            except Exception:
                self.root.after(0, lambda: Toast(self.root, "RFID: koneksi gagal", RED))
                return
            if d.get("success"):
                cmap = {1: GREEN, 2: ORANGE, 3: BLUE_SOFT, 4: PURPLE_SOFT}
                msg = d["message"]
                col = cmap.get(d.get("case"), GREEN)
                self.root.after(0, lambda: Toast(self.root, msg, col))
            else:
                msg = d.get("message", "Gagal")
                self.root.after(0, lambda: Toast(self.root, msg, RED))

        threading.Thread(target=_worker, daemon=True).start()

    # ──────────────────────────────────────────────────────
    #  DATA LOADING
    # ──────────────────────────────────────────────────────
    def _load_orders(self):
        def _worker():
            try:
                req = _get_requests()
                r = req.get(f"{API_URL}?action=get_orders", timeout=6)
                j = r.json()
            except Exception:
                self.root.after(0, self._on_load_fail)
                return
            if not j.get("success"):
                self.root.after(0, self._on_load_fail)
                return
            orders = j["data"]
            self.root.after(0, lambda: self._on_load_ok(orders))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_load_fail(self):
        self._offline()
        self.board.set_data([])
        self._update_page_label()
        self._schedule_data_refresh()

    def _on_load_ok(self, orders):
        self._online()
        self.board.set_data(orders)
        b = sum(1 for o in orders if "Baru" in o.get("status_order", ""))
        p = len(orders) - b
        self.cnt_lbl.config(text=f"BARU {b}  ·  DIPROSES {p}")
        self._update_page_label()
        self._schedule_page_flip()
        self._schedule_data_refresh()

    def _schedule_data_refresh(self):
        if self._data_refresh_job:
            self.root.after_cancel(self._data_refresh_job)
        self._data_refresh_job = self.root.after(REFRESH_SEC * 1000, self._load_orders)

    def _schedule_page_flip(self):
        if self._page_flip_job:
            self.root.after_cancel(self._page_flip_job)
        self._page_flip_job = self.root.after(PAGE_FLIP_SEC * 1000, self._flip_page)

    def _flip_page(self):
        flipped = self.board.next_page()
        self._update_page_label()
        if flipped:
            self._schedule_page_flip()
        else:
            self._page_flip_job = self.root.after(2000, self._flip_page)

    def _update_page_label(self):
        total = len(self.board.pages)
        curr = self.board.current_page + 1
        self.page_lbl.config(text="" if total <= 1 else f"PAGE {curr}/{total}")

    def _online(self):
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 11, 11, fill=GREEN, outline="")

    def _offline(self):
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 11, 11, fill=RED, outline="")
        self.cnt_lbl.config(text="OFFLINE")

    def _tick_clock(self):
        self.clk_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw()

    splash = SplashScreen(root)
    root.update()

    AzzahraBoard(root, splash)

    root.deiconify()
    root.mainloop()