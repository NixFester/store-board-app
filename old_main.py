"""
Store Board App
================
Kiosk Mode + Auto Pagination + Horizontal Image Cycling + Auto-Update
Light theme optimised for daylight visibility on slow hardware.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
import sys
import os
import json
import tempfile
import zipfile
import subprocess
import shutil
import glob

# ── Lazy imports ──────────────────────────────────────────
_requests = None
def _get_requests():
    global _requests
    if _requests is None:
        import requests as _req
        _requests = _req
    return _requests

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Path resolution (frozen vs source) ────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR  = os.path.dirname(sys.executable)
    _INTERNAL = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
    _INTERNAL = BASE_DIR

ASSETS_DIR   = os.path.join(BASE_DIR, 'assets')
LOGO_PATH    = os.path.join(ASSETS_DIR, 'logo.jpg')
VERSION_FILE = os.path.join(BASE_DIR, 'version.txt')
EXE_NAME     = 'store-board-app.exe'

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
API_URL         = "http://azzahracomputertegal.com/apipy/api.php"
REFRESH_SEC     = 30
PAGE_FLIP_SEC   = 16
IMAGE_CYCLE_SEC = 6
TOAST_MS        = 4000
RFID_TIMEOUT    = 500

# ── Branding ───────────────────────────────────────────────
STORE_NAME    = "AZZAHRA COMPUTER"
FLAVOR_TEXT   = "Service Center #1"
WEBSITE_URL   = "https://website.azzahracomputertegal.com/"
WEBSITE_SHORT = "website.azzahracomputertegal.com"
CONTACT_NUM   = "+62 859-4200-1720"

# ── Auto-Update Config ────────────────────────────────────
AUTO_UPDATE_ENABLED   = True
UPDATE_CHECK_DELAY    = 15
UPDATE_CHECK_INTERVAL = 1800
UPDATE_METHOD         = "github"

data = {}
with open("config.txt") as f:
    exec(f.read(), data)

GITHUB_OWNER = data["owner"]
GITHUB_REPO  = data["repo"]

WEBSITE_VERSION_URL = "http://azzahracomputertegal.com/version.txt"
WEBSITE_DIST_URL    = "http://azzahracomputertegal.com/dist.zip"

# ── Version ───────────────────────────────────────────────
def get_current_version():
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"

CURRENT_VERSION = get_current_version()

def compare_versions(v1, v2):
    try:
        p1 = [int(x) for x in v1.lstrip('v').split('.')]
        p2 = [int(x) for x in v2.lstrip('v').split('.')]
    except Exception:
        return 0
    while len(p1) < len(p2): p1.append(0)
    while len(p2) < len(p1): p2.append(0)
    for a, b in zip(p1, p2):
        if a > b: return 1
        if a < b: return -1
    return 0

# ── Indonesian locale ─────────────────────────────────────
HARI_INDO  = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN_INDO = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# ═══════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════
BG          = "#f5f7fa"
HEADER_BG   = "#e4e8ee"
ROW_ALT     = "#edf0f4"
GRID        = "#cdd4dc"
GRID_MED    = "#b4bcc6"
AMBER       = "#d49500"
AMBER_DIM   = "#a87800"
TEXT        = "#3d4f5f"
TEXT_BRIGHT = "#1a2533"
TEXT_DIM    = "#8896a6"
GREEN       = "#00884a"
GREEN_BG    = "#daf5e6"
GREEN_BD    = "#6fcf97"
ORANGE      = "#d97706"
ORANGE_BG   = "#fef3dc"
ORANGE_BD   = "#f5c563"
RED         = "#c62828"
BLUE_SOFT   = "#2563eb"
PURPLE_SOFT = "#6d5fcb"
PANEL_BG    = "#ffffff"

PAD     = 18
HDR_H   = 52
LOGO_SZ = 80

# ═══════════════════════════════════════════════════════════
#  TUNING  — everything you might want to tweak
#  Change these values; nothing else needs editing.
# ═══════════════════════════════════════════════════════════

# ── Overall layout split (top panel vs table) ─────────────
# These are grid row weights — ratio between the two zones.
# e.g. TOP_WEIGHT=4, TABLE_WEIGHT=7 → top gets 4/11 of height
LAYOUT_TOP_WEIGHT   = 2
LAYOUT_TABLE_WEIGHT = 8

# ── Top panel column split (info vs promo image) ──────────
# Grid column weights. Higher = wider.
LAYOUT_INFO_WEIGHT  = 35   # left  — store info
LAYOUT_PROMO_WEIGHT = 65   # right — promo image

# ── Info panel row weights ────────────────────────────────
# Controls how much vertical space each section claims.
INFO_ROW_BRANDING = 5   # logo + name + flavor
INFO_ROW_CLOCK    = 3   # HH:MM:SS
INFO_ROW_DATE     = 2   # day + date string
INFO_ROW_WEBSITE  = 1   # website URL
INFO_ROW_CONTACT  = 1   # phone number

# ── Info panel font scale factors (multiplied by panel height) ──
# Increase to make text bigger, decrease to shrink it.
INFO_FS_NAME    = 0.10   # store name
INFO_FS_FLAVOR  = 0.05   # flavor / tagline
INFO_FS_CLOCK   = 0.09   # clock digits
INFO_FS_DATE    = 0.038  # date string
INFO_FS_CONTACT = 0.032  # website + phone

# ── Info panel logo width (fraction of panel width) ───────
INFO_LOGO_W_FRAC = 0.32   # 0.0–1.0  (0.32 = 32 % of panel width)

# ── Info panel padding ────────────────────────────────────
INFO_PAD_OUTER  = 14   # px — padding around branding block and sides
INFO_PAD_BOTTOM = 14   # px — bottom padding on contact row

# ── Table ─────────────────────────────────────────────────
TABLE_ROWS_PER_PAGE = 5       # fixed rows always shown
TABLE_HDR_HEIGHT    = 52      # px — header bar height

# Table column widths in pixels (0 = fill remaining space)
TABLE_COL_NO       = 80
TABLE_COL_CUSTOMER = 280
TABLE_COL_KELUHAN  = 0        # fills all remaining width
TABLE_COL_STATUS   = 180
TABLE_COL_WAIT     = 120

# ── Table font scale factors (multiplied by row height) ───
TABLE_FS_NUM    = 0.30   # row number
TABLE_FS_NAME   = 0.28   # customer name
TABLE_FS_KEL    = 0.22   # keluhan / complaint
TABLE_FS_STATUS = 0.22   # status badge text
TABLE_FS_WAIT   = 0.28   # wait days
TABLE_FS_HDR    = 0.22   # column header labels

# ── Table status badge vertical padding (fraction of row height) ──
TABLE_BADGE_PAD_Y = 0.15   # 0.0–0.5

# ── Footer bar height ─────────────────────────────────────
FOOTER_H = 36   # px

# ── Derived — do not edit below this line ─────────────────
COLS = [
    ("NO",       TABLE_COL_NO),
    ("CUSTOMER", TABLE_COL_CUSTOMER),
    ("KELUHAN",  TABLE_COL_KELUHAN),
    ("STATUS",   TABLE_COL_STATUS),
    ("WAIT",     TABLE_COL_WAIT),
]


# ═══════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ═══════════════════════════════════════════════════════════
class SplashScreen:
    def __init__(self, root: tk.Tk):
        self.root   = root
        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w, h = 460, 220
        self.splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.splash.configure(bg=HEADER_BG)

        outer = tk.Frame(self.splash, bg=AMBER, padx=2, pady=2)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=HEADER_BG)
        inner.pack(fill="both", expand=True)

        logo_loaded = False
        if HAS_PIL and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img.thumbnail((64, 64), Image.LANCZOS)
                self._splash_logo = ImageTk.PhotoImage(img)
                tk.Label(inner, image=self._splash_logo,
                         bg=HEADER_BG).pack(pady=(24, 4))
                logo_loaded = True
            except Exception:
                pass

        if not logo_loaded:
            tk.Label(inner, text=STORE_NAME,
                     font=("Consolas", 28, "bold"),
                     bg=HEADER_BG, fg=AMBER).pack(pady=(24, 0))

        tk.Label(inner, text="LOADING…",
                 font=("Consolas", 10), bg=HEADER_BG, fg=TEXT_DIM).pack()

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
        self.frame  = tk.Frame(parent, bg="#ffffff",
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
        if left <= 0: return
        try:
            self.bar.place(relx=0, rely=1.0,
                           relwidth=max(left / TOAST_MS, 0), anchor="sw")
            self.parent.after(40, self._shrink, left - 40)
        except tk.TclError:
            pass

    def _destroy(self):
        try: self.frame.destroy()
        except tk.TclError: pass


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
#  BOARD CANVAS  — fixed 5 rows, fonts scale to fill height
# ═══════════════════════════════════════════════════════════
class BoardCanvas(tk.Canvas):
    ROWS_PER_PAGE = TABLE_ROWS_PER_PAGE

    def __init__(self, master, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, **kw)
        self.full_orders  = []
        self.pages        = [[]]
        self.current_page = 0
        self.cx = []
        self.cw = []

    # ── public API ────────────────────────────────────────
    def set_data(self, orders):
        self.full_orders  = orders
        self.current_page = 0
        self._paginate()

    def update_cols(self, cx, cw):
        self.cx, self.cw = cx, cw

    def next_page(self):
        if len(self.pages) <= 1:
            return False
        self.current_page = (self.current_page + 1) % len(self.pages)
        self._draw()
        return True

    # ── internals ─────────────────────────────────────────
    def _row_h(self):
        h = self.winfo_height()
        return max(40, h // self.ROWS_PER_PAGE)

    def _paginate(self):
        n = self.ROWS_PER_PAGE
        orders = self.full_orders
        self.pages = [orders[i:i + n] for i in range(0, max(len(orders), 1), n)]
        if not self.pages:
            self.pages = [[]]
        if self.current_page >= len(self.pages):
            self.current_page = 0
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 80 or h < 80 or not self.cx:
            return

        rh        = self._row_h()
        page_data = self.pages[self.current_page] if self.current_page < len(self.pages) else []

        if not page_data:
            fs = max(12, rh // 3)
            self.create_text(w // 2, h // 2,
                             text="— Loading... —",
                             font=("Consolas", fs, "bold"),
                             fill=TEXT_DIM, anchor="center")
            return

        for slot in range(self.ROWS_PER_PAGE):
            order = page_data[slot] if slot < len(page_data) else None
            self._draw_row(slot * rh, rh, order, slot)

    def _draw_row(self, y, rh, o, idx):
        w  = self.winfo_width()
        cy = y + rh // 2

        # stripe + bottom border
        if idx % 2 == 1:
            self.create_rectangle(0, y, w, y + rh, fill=ROW_ALT, outline="")
        self.create_line(0, y + rh, w, y + rh, fill=GRID)

        # vertical dividers
        for xi in self.cx[1:-1]:
            self.create_line(xi, y, xi, y + rh, fill=GRID)

        if o is None:
            return  # empty slot — stripe only

        # font sizes — all derived from row height
        fs_num    = max(10, int(rh * TABLE_FS_NUM))
        fs_name   = max(10, int(rh * TABLE_FS_NAME))
        fs_kel    = max(8,  int(rh * TABLE_FS_KEL))
        fs_status = max(8,  int(rh * TABLE_FS_STATUS))
        fs_wait   = max(10, int(rh * TABLE_FS_WAIT))

        # NO
        xi, cw = self.cx[0], self.cw[0]
        self.create_text(xi + cw // 2, cy,
                         text=f"{idx + 1:02d}",
                         font=("Consolas", fs_num),
                         fill=TEXT_DIM, anchor="center")

        # CUSTOMER
        xi, cw = self.cx[1], self.cw[1]
        nama = self._fit(o.get("nama_customer", "-"), cw, fs_name)
        self.create_text(xi + PAD, cy,
                         text=nama,
                         font=("Consolas", fs_name, "bold"),
                         fill=TEXT_BRIGHT, anchor="w")

        # KELUHAN
        xi, cw = self.cx[2], self.cw[2]
        raw = o.get("keluhan", "-").replace("\n", ", ").replace("\r", "")
        kel = self._fit(raw, cw, fs_kel)
        self.create_text(xi + PAD, cy,
                         text=kel,
                         font=("Consolas", fs_kel),
                         fill=TEXT, anchor="w")

        # STATUS badge
        xi, cw = self.cx[3], self.cw[3]
        st = o.get("status_order", "")
        if "Baru" in st:
            bg, fg, bd, lbl = GREEN_BG, GREEN, GREEN_BD, "● BARU"
        else:
            bg, fg, bd, lbl = ORANGE_BG, ORANGE, ORANGE_BD, "● DIPROSES"
        py  = max(6, int(rh * TABLE_BADGE_PAD_Y))
        px  = 10
        bx  = xi + px
        by  = y  + py
        bw  = cw - px * 2
        bh  = rh - py * 2
        self.create_rectangle(bx, by, bx + bw, by + bh,
                              fill=bg, outline=bd)
        self.create_text(bx + bw // 2, by + bh // 2,
                         text=lbl,
                         font=("Consolas", fs_status, "bold"),
                         fill=fg, anchor="center")

        # WAIT
        xi, cw = self.cx[4], self.cw[4]
        hari = int(o.get("hari_menunggu", 0))
        if hari == 0:
            txt, fg = "TODAY", AMBER
        elif hari == 1:
            txt, fg = "1 HARI", TEXT
        else:
            txt = f"{hari} HARI"
            fg  = RED if hari > 7 else (ORANGE if hari > 3 else TEXT)
        self.create_text(xi + cw - PAD, cy,
                         text=txt,
                         font=("Consolas", fs_wait, "bold"),
                         fill=fg, anchor="e")

    @staticmethod
    def _fit(text, col_w, fsize):
        ch = max(1, int((col_w - PAD * 2) / (fsize * 0.62)))
        return text if len(text) <= ch else text[:ch - 2] + ".."


# ═══════════════════════════════════════════════════════════
#  IMAGE CYCLER — stretch to fill exactly, no aspect ratio
# ═══════════════════════════════════════════════════════════
class ImageCycler:
    VALID_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')

    def __init__(self, canvas):
        self.canvas        = canvas
        self.raw_images    = []
        self.photo_refs    = []
        self.current_index = 0
        self.panel_w       = 800
        self.panel_h       = 400
        self._cycle_job    = None
        self._load_images()

    def _load_images(self):
        self.raw_images = []
        if not os.path.isdir(ASSETS_DIR):
            os.makedirs(ASSETS_DIR, exist_ok=True)
            return
        for f in sorted(os.listdir(ASSETS_DIR)):
            if f.lower() == 'logo.jpg':
                continue
            if f.lower().endswith(self.VALID_EXTS):
                try:
                    img = Image.open(os.path.join(ASSETS_DIR, f))
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    self.raw_images.append((f, img))
                except Exception:
                    pass

    def resize_all(self, w, h):
        self.panel_w    = max(w, 50)
        self.panel_h    = max(h, 50)
        self.photo_refs = []
        for _name, img in self.raw_images:
            try:
                # Stretch to fill exactly — no bars, no crop, no aspect ratio
                stretched = img.resize((self.panel_w, self.panel_h), Image.LANCZOS)
                self.photo_refs.append(ImageTk.PhotoImage(stretched))
            except Exception:
                self.photo_refs.append(None)
        self.show_current()

    def show_current(self):
        self.canvas.delete("all")
        w = self.panel_w
        h = self.panel_h
        if not self.photo_refs or self.photo_refs[self.current_index] is None:
            self.canvas.create_text(
                w // 2, h // 2,
                text="No Promotional Images\nPlace images in\nassets/ folder",
                font=("Consolas", 16), fill=TEXT_DIM, justify="center")
            return
        self.canvas.create_image(0, 0, anchor="nw",
                                 image=self.photo_refs[self.current_index])

    def next_image(self):
        if self.photo_refs:
            self.current_index = (self.current_index + 1) % len(self.photo_refs)
        self.show_current()

    def start_cycling(self):
        self._cycle_job = self.canvas.after(
            IMAGE_CYCLE_SEC * 1000, self._cycle_tick)

    def _cycle_tick(self):
        self.next_image()
        self._cycle_job = self.canvas.after(
            IMAGE_CYCLE_SEC * 1000, self._cycle_tick)

    def stop_cycling(self):
        if self._cycle_job:
            self.canvas.after_cancel(self._cycle_job)
            self._cycle_job = None


# ═══════════════════════════════════════════════════════════
#  AUTO UPDATER
# ═══════════════════════════════════════════════════════════
class AutoUpdater:
    def __init__(self, root, on_status_update=None):
        self.root             = root
        self.on_status_update = on_status_update or (lambda msg: None)
        self._check_job       = None
        self._updating        = False

    def schedule_check(self, delay_sec=UPDATE_CHECK_DELAY):
        self._check_job = self.root.after(
            delay_sec * 1000, self._check_for_updates)

    def _check_for_updates(self):
        if not AUTO_UPDATE_ENABLED or self._updating:
            self._check_job = self.root.after(
                UPDATE_CHECK_INTERVAL * 1000, self._check_for_updates)
            return
        threading.Thread(target=self._check_worker, daemon=True).start()

    def _check_worker(self):
        try:
            if UPDATE_METHOD == "github": self._check_github()
            else:                         self._check_website()
        except Exception:
            pass
        finally:
            self._check_job = self.root.after(
                UPDATE_CHECK_INTERVAL * 1000, self._check_for_updates)

    def _check_github(self):
        req     = _get_requests()
        api_url = (f"https://api.github.com/repos/"
                   f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest")
        r       = req.get(api_url, timeout=15,
                          headers={"Accept": "application/vnd.github.v3+json"})
        data    = r.json()
        remote  = data.get("tag_name", "").lstrip('v')

        if compare_versions(remote, CURRENT_VERSION) <= 0:
            self._status(f"v{CURRENT_VERSION} — up to date")
            return

        self._status(f"Update v{remote} available…")
        self.root.after(0,
            lambda: Toast(self.root, f"Update v{remote} — downloading…", BLUE_SOFT))

        download_url = None
        for asset in data.get("assets", []):
            if asset["name"] == "dist.zip":
                download_url = asset["browser_download_url"]
                break
        if not download_url:
            return
        self._download_and_apply(download_url, remote)

    def _check_website(self):
        req    = _get_requests()
        r      = req.get(WEBSITE_VERSION_URL, timeout=15)
        remote = r.text.strip().lstrip('v')

        if compare_versions(remote, CURRENT_VERSION) <= 0:
            self._status(f"v{CURRENT_VERSION} — up to date")
            return

        self._status(f"Update v{remote} available…")
        self.root.after(0,
            lambda: Toast(self.root, f"Update v{remote} — downloading…", BLUE_SOFT))
        self._download_and_apply(WEBSITE_DIST_URL, remote)

    def _download_and_apply(self, url, remote_version):
        if self._updating:
            return
        self._updating = True
        try:
            req     = _get_requests()
            tmp_zip = os.path.join(tempfile.gettempdir(), "store_board_update.zip")
            self._status("Downloading update…")

            r = req.get(url, timeout=120, stream=True)
            r.raise_for_status()
            total      = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(tmp_zip, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        self._status(f"Downloading… {downloaded * 100 // total}%")

            self._status("Extracting update…")
            extract_dir = os.path.join(tempfile.gettempdir(), "store_board_update")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)

            with zipfile.ZipFile(tmp_zip, 'r') as zf:
                zf.extractall(extract_dir)
            os.remove(tmp_zip)

            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(
                    os.path.join(extract_dir, contents[0])):
                extract_dir = os.path.join(extract_dir, contents[0])

            self._status("Applying update…")
            self.root.after(0,
                lambda: Toast(self.root, "Update ready — restarting…", GREEN))
            self.root.after(3000,
                lambda: self._apply_update(extract_dir))

        except Exception as e:
            self._updating = False
            self._status(f"Update failed: {e}")
            self.root.after(0,
                lambda: Toast(self.root, f"Update failed: {e}", RED))

    def _apply_update(self, update_dir):
        try:
            exe_path = (sys.executable if getattr(sys, 'frozen', False)
                        else os.path.join(BASE_DIR, "main.py"))
            exe_name   = os.path.basename(exe_path)
            batch_path = os.path.join(tempfile.gettempdir(),
                                      "store_board_updater.bat")
            batch_content = f'''@echo off
setlocal
set "APP_DIR={BASE_DIR}"
set "UPDATE_DIR={update_dir}"
set "EXE_NAME={exe_name}"
echo Updating Store Board App...
timeout /t 3 /nobreak >nul
taskkill /f /im "{exe_name}" 2>nul
timeout /t 2 /nobreak >nul
xcopy /s /e /y /i "%UPDATE_DIR%\\*" "%APP_DIR%\\" >nul 2>&1
rd /s /q "%UPDATE_DIR%" 2>nul
echo Update complete. Restarting...
start "" "%APP_DIR%\\{exe_name}"
(goto) 2>nul & del "%~f0"
'''
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            subprocess.Popen(['cmd', '/c', batch_path],
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             cwd=tempfile.gettempdir())
            self.root.after(500, self.root.quit)
        except Exception:
            self._updating = False

    def _status(self, msg):
        try:
            self.root.after(0, lambda: self.on_status_update(msg))
        except Exception:
            pass

    def check_now(self):
        if self._updating:
            return
        self._status("Checking for updates…")
        threading.Thread(target=self._check_worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════
class AzzahraBoard:

    def __init__(self, root: tk.Tk, splash: SplashScreen):
        self.root   = root
        self.splash = splash
        self.root.title("Store Board App")
        self.root.configure(bg=BG)

        self.cx, self.cw    = calc_cols(1200)
        self._rfid_timer    = None
        self._page_flip_job = None
        self._data_refresh_job = None
        self._resize_job    = None
        self._img_resize_job = None
        self._logo_photo    = None
        self.cycler         = None
        self.updater        = None

        self._build_ui()
        self._build_footer()
        self._build_hidden_rfid()

        self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)
        self.root.update_idletasks()

        self.root.bind("<Escape>",    lambda e: self.root.quit())
        self.root.bind("<Control-u>", lambda e: self._manual_update_check())

        self.splash.finish()
        self._tick_clock()
        self.root.after(200,  self._load_orders)
        self.root.after(500,  self._init_image_cycler)
        self.root.after(800,  self._init_auto_updater)

    # ══════════════════════════════════════════════════════
    #  UI SKELETON
    #
    #  ┌──────────────────────────────────────────────────┐
    #  │  [info panel 35%]  │  [promo image 65%]         │  row 0 weight=4
    #  ├──────────────────────────────────────────────────┤  amber bar
    #  │           service order table                    │  row 2 weight=7
    #  └──────────────────────────────────────────────────┘
    # ══════════════════════════════════════════════════════
    def _build_ui(self):
        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        content.grid_rowconfigure(0, weight=LAYOUT_TOP_WEIGHT)
        content.grid_rowconfigure(1, weight=0)
        content.grid_rowconfigure(2, weight=LAYOUT_TABLE_WEIGHT)
        content.grid_columnconfigure(0, weight=LAYOUT_INFO_WEIGHT,  minsize=320)
        content.grid_columnconfigure(1, weight=LAYOUT_PROMO_WEIGHT, minsize=440)

        # ── Info panel (left) ──────────────────────────
        info_border = tk.Frame(content, bg=AMBER)
        info_border.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        info_bg = tk.Frame(info_border, bg=PANEL_BG)
        info_bg.pack(fill="both", expand=True, padx=3, pady=3)
        self._build_info_panel(info_bg)

        # ── Promo image (right) ────────────────────────
        promo_border = tk.Frame(content, bg=AMBER)
        promo_border.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        promo_bg = tk.Frame(promo_border, bg=PANEL_BG)
        promo_bg.pack(fill="both", expand=True, padx=3, pady=3)

        self.img_canvas = tk.Canvas(promo_bg, bg=PANEL_BG, highlightthickness=0)
        self.img_canvas.pack(fill="both", expand=True)
        self.img_canvas.bind("<Configure>", self._on_img_resize)

        # ── Amber separator ────────────────────────────
        tk.Frame(content, bg=AMBER, height=3).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 6))

        # ── Table (bottom) ─────────────────────────────
        table_border = tk.Frame(content, bg=AMBER)
        table_border.grid(row=2, column=0, columnspan=2, sticky="nsew")
        table_bg = tk.Frame(table_border, bg=BG)
        table_bg.pack(fill="both", expand=True, padx=3, pady=3)

        self.hdr = tk.Canvas(table_bg, bg=HEADER_BG, height=TABLE_HDR_HEIGHT,
                             highlightthickness=0)
        self.hdr.pack(fill="x")
        tk.Frame(table_bg, bg=GRID_MED, height=1).pack(fill="x")

        self.board = BoardCanvas(table_bg)
        self.board.pack(fill="both", expand=True)
        self.board.bind("<Configure>", self._on_board_resize)

    # ══════════════════════════════════════════════════════
    #  INFO PANEL
    #
    #  Uses grid to lay out:
    #    row 0 weight=5  →  branding block  [logo | name / flavor]
    #    row 1 weight=0  →  divider
    #    row 2 weight=3  →  clock
    #    row 3 weight=2  →  date
    #    row 4 weight=1  →  website
    #    row 5 weight=1  →  contact
    #
    #  All fonts recalculated in _on_info_resize via <Configure>.
    # ══════════════════════════════════════════════════════
    def _build_info_panel(self, parent):
        outer = tk.Frame(parent, bg=PANEL_BG)
        outer.pack(fill="both", expand=True)
        self._info_outer = outer

        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=INFO_ROW_BRANDING)  # branding
        outer.grid_rowconfigure(1, weight=0)                  # divider
        outer.grid_rowconfigure(2, weight=INFO_ROW_CLOCK)     # clock
        outer.grid_rowconfigure(3, weight=INFO_ROW_DATE)      # date
        outer.grid_rowconfigure(4, weight=INFO_ROW_WEBSITE)   # website
        outer.grid_rowconfigure(5, weight=INFO_ROW_CONTACT)   # contact

        # ── Branding block ─────────────────────────────
        brand = tk.Frame(outer, bg=PANEL_BG)
        brand.grid(row=0, column=0, sticky="nsew",
                   padx=INFO_PAD_OUTER, pady=(INFO_PAD_OUTER, 6))
        self._brand_frame = brand

        brand.grid_columnconfigure(0, weight=0)   # logo — width set dynamically
        brand.grid_columnconfigure(1, weight=1)   # text fills rest
        brand.grid_rowconfigure(0, weight=1)      # name row
        brand.grid_rowconfigure(1, weight=1)      # flavor row

        # Logo canvas — rowspan 2, width is set dynamically in resize handler
        self.logo_canvas = tk.Canvas(brand, bg=PANEL_BG, highlightthickness=0,
                                     width=LOGO_SZ)
        self.logo_canvas.grid(row=0, column=0, rowspan=2,
                              sticky="nsew", padx=(0, 14))
        self.logo_canvas.bind("<Configure>", lambda e: self._load_logo())

        # Store name — anchored to south-west of its cell (flush against flavor)
        self.store_name_lbl = tk.Label(brand, text=STORE_NAME,
                                       font=("Consolas", 28, "bold"),
                                       bg=PANEL_BG, fg=AMBER, anchor="sw")
        self.store_name_lbl.grid(row=0, column=1, sticky="sew")

        # Flavor text — anchored to north-west (flush under name)
        self.flavor_lbl = tk.Label(brand, text=FLAVOR_TEXT,
                                   font=("Consolas", 14, "bold"),
                                   bg=PANEL_BG, fg=AMBER_DIM, anchor="nw")
        self.flavor_lbl.grid(row=1, column=1, sticky="new")

        # ── Divider ────────────────────────────────────
        tk.Frame(outer, bg=GRID_MED, height=1).grid(
            row=1, column=0, sticky="ew", padx=INFO_PAD_OUTER)

        # ── Clock ──────────────────────────────────────
        self.clock_lbl = tk.Label(outer, font=("Consolas", 32, "bold"),
                                   bg=PANEL_BG, fg=TEXT_BRIGHT, anchor="w")
        self.clock_lbl.grid(row=2, column=0, sticky="nsew", padx=INFO_PAD_OUTER)

        # ── Date ───────────────────────────────────────
        self.date_lbl = tk.Label(outer, font=("Consolas", 12),
                                  bg=PANEL_BG, fg=TEXT_DIM, anchor="w")
        self.date_lbl.grid(row=3, column=0, sticky="nsew", padx=INFO_PAD_OUTER)

        # ── Website ────────────────────────────────────
        self.web_lbl = tk.Label(outer, text=f"🌐 {WEBSITE_SHORT}",
                                 font=("Consolas", 10),
                                 bg=PANEL_BG, fg=BLUE_SOFT, anchor="w")
        self.web_lbl.grid(row=4, column=0, sticky="nsew", padx=INFO_PAD_OUTER)

        # ── Contact ────────────────────────────────────
        self.contact_lbl = tk.Label(outer, text=f"📞 {CONTACT_NUM}",
                                     font=("Consolas", 10, "bold"),
                                     bg=PANEL_BG, fg=TEXT, anchor="w")
        self.contact_lbl.grid(row=5, column=0, sticky="nsew",
                               padx=INFO_PAD_OUTER, pady=(0, INFO_PAD_BOTTOM))

        outer.bind("<Configure>", self._on_info_resize)

    def _on_info_resize(self, e=None):
        h = self._info_outer.winfo_height()
        w = self._info_outer.winfo_width()
        if h < 50 or w < 50:
            return

        logo_w = max(40, int(w * INFO_LOGO_W_FRAC))
        self.logo_canvas.config(width=logo_w)

        self.store_name_lbl.config(
            font=("Consolas", max(10, int(h * INFO_FS_NAME)),    "bold"))
        self.flavor_lbl.config(
            font=("Consolas", max(8,  int(h * INFO_FS_FLAVOR)),  "bold"))
        self.clock_lbl.config(
            font=("Consolas", max(10, int(h * INFO_FS_CLOCK)),   "bold"))
        self.date_lbl.config(
            font=("Consolas", max(7,  int(h * INFO_FS_DATE))))
        self.web_lbl.config(
            font=("Consolas", max(7,  int(h * INFO_FS_CONTACT))))
        self.contact_lbl.config(
            font=("Consolas", max(7,  int(h * INFO_FS_CONTACT)), "bold"))

    def _load_logo(self):
        self.logo_canvas.delete("all")
        w  = self.logo_canvas.winfo_width()
        h  = self.logo_canvas.winfo_height()
        if w < 10 or h < 10:
            return
        sz = min(w, h)
        if HAS_PIL and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img = img.resize((sz, sz), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(img)
                self.logo_canvas.create_image(
                    (w - sz) // 2, (h - sz) // 2,
                    anchor="nw", image=self._logo_photo)
                return
            except Exception:
                pass
        self._logo_photo = None
        p  = 4
        fs = max(10, sz // 3)
        self.logo_canvas.create_rectangle(p, p, sz - p, sz - p,
                                          fill=AMBER, outline=AMBER_DIM, width=2)
        self.logo_canvas.create_text(sz // 2, sz // 2, text="AC",
                                     font=("Consolas", fs, "bold"),
                                     fill="white")

    # ══════════════════════════════════════════════════════
    #  RESIZE HANDLERS
    # ══════════════════════════════════════════════════════
    def _on_board_resize(self, _e=None):
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(80, self._apply_board_resize)

    def _apply_board_resize(self):
        self._resize_job = None
        w = self.board.winfo_width()
        h = self.board.winfo_height()
        if w < 80 or h < 80:
            return
        self.cx, self.cw = calc_cols(w)
        self.board.update_cols(self.cx, self.cw)
        self._draw_headers()
        self.board._paginate()

    def _on_img_resize(self, _e=None):
        if self._img_resize_job:
            self.root.after_cancel(self._img_resize_job)
        self._img_resize_job = self.root.after(120, self._apply_img_resize)

    def _apply_img_resize(self):
        self._img_resize_job = None
        if not self.cycler:
            return
        w = self.img_canvas.winfo_width()
        h = self.img_canvas.winfo_height()
        if w < 50 or h < 50:
            return
        self.cycler.resize_all(w, h)

    def _draw_headers(self):
        self.hdr.delete("all")
        if not self.cx:
            return
        w = self.hdr.winfo_width()
        if w < 80:
            return
        rh = self.board._row_h() if self.board.winfo_height() > 80 else TABLE_HDR_HEIGHT
        fs = max(9, int(rh * TABLE_FS_HDR))
        cy = TABLE_HDR_HEIGHT // 2
        for i, (name, _) in enumerate(COLS):
            xi = self.cx[i]
            self.hdr.create_text(xi + PAD, cy,
                                 text=name,
                                 font=("Consolas", fs, "bold"),
                                 fill=AMBER, anchor="w")
            if 0 < i < len(COLS) - 1:
                self.hdr.create_line(xi, 0, xi, HDR_H, fill=GRID)

    # ══════════════════════════════════════════════════════
    #  FOOTER
    # ══════════════════════════════════════════════════════
    def _build_footer(self):
        bar = tk.Frame(self.root, bg=HEADER_BG, height=FOOTER_H)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=HEADER_BG)
        left.pack(side="left", padx=(20, 0), pady=7)

        self.dot = tk.Canvas(left, width=12, height=12,
                             bg=HEADER_BG, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 6))
        self.dot.create_oval(1, 1, 11, 11, fill=GREEN, outline="")

        self.status_lbl = tk.Label(left, text="ONLINE",
                                   font=("Consolas", 9, "bold"),
                                   bg=HEADER_BG, fg=TEXT_DIM)
        self.status_lbl.pack(side="left", padx=(0, 16))

        self.cnt_lbl = tk.Label(left, text="",
                                font=("Consolas", 9),
                                bg=HEADER_BG, fg=TEXT_DIM)
        self.cnt_lbl.pack(side="left", padx=(0, 16))

        self.page_lbl = tk.Label(left, text="",
                                 font=("Consolas", 9),
                                 bg=HEADER_BG, fg=AMBER_DIM)
        self.page_lbl.pack(side="left")

        right = tk.Frame(bar, bg=HEADER_BG)
        right.pack(side="right", padx=(0, 20), pady=7)

        self.update_lbl = tk.Label(right, text=f"v{CURRENT_VERSION}",
                                   font=("Consolas", 9),
                                   bg=HEADER_BG, fg=TEXT_DIM)
        self.update_lbl.pack(side="right")

    # ══════════════════════════════════════════════════════
    #  IMAGE CYCLER INIT
    # ══════════════════════════════════════════════════════
    def _init_image_cycler(self):
        if not HAS_PIL:
            self.img_canvas.create_text(
                400, 200,
                text="Install Pillow\nfor image display",
                font=("Consolas", 14), fill=TEXT_DIM, justify="center")
            return
        self.cycler = ImageCycler(self.img_canvas)
        self.root.after(200, self._apply_img_resize)
        self.root.after(1000,
            lambda: self.cycler.start_cycling() if self.cycler else None)

    # ══════════════════════════════════════════════════════
    #  AUTO UPDATER INIT
    # ══════════════════════════════════════════════════════
    def _init_auto_updater(self):
        self.updater = AutoUpdater(self.root,
                                   on_status_update=self._on_update_status)
        self.updater.schedule_check()

    def _on_update_status(self, msg):
        self.update_lbl.config(text=f"v{CURRENT_VERSION}  —  {msg}")

    def _manual_update_check(self):
        if self.updater:
            Toast(self.root, "Checking for updates…", BLUE_SOFT)
            self.updater.check_now()

    # ══════════════════════════════════════════════════════
    #  HIDDEN RFID INPUT
    # ══════════════════════════════════════════════════════
    def _build_hidden_rfid(self):
        self.rfid = tk.Entry(self.root, width=1,
                             bg=BG, fg=BG, insertbackground=BG,
                             bd=0, highlightthickness=0, relief="flat")
        self.rfid.place(x=-50, y=-50)
        self.rfid.bind("<Return>",    self._rfid_enter)
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
                r   = req.post(f"{API_URL}?action=scan_rfid",
                               json={"nokartu": nokartu}, timeout=6)
                d   = r.json()
            except Exception:
                self.root.after(0, lambda:
                    Toast(self.root, "RFID: koneksi gagal", RED))
                return
            if d.get("success"):
                cmap = {1: GREEN, 2: ORANGE, 3: BLUE_SOFT, 4: PURPLE_SOFT}
                msg  = d["message"]
                col  = cmap.get(d.get("case"), GREEN)
                self.root.after(0, lambda: Toast(self.root, msg, col))
            else:
                msg = d.get("message", "Gagal")
                self.root.after(0, lambda: Toast(self.root, msg, RED))
        threading.Thread(target=_worker, daemon=True).start()

    # ══════════════════════════════════════════════════════
    #  DATA LOADING
    # ══════════════════════════════════════════════════════
    def _load_orders(self):
        def _worker():
            try:
                req = _get_requests()
                r   = req.get(f"{API_URL}?action=get_orders", timeout=6)
                j   = r.json()
            except Exception:
                self.root.after(0, self._on_load_fail)
                return
            if not j.get("success"):
                self.root.after(0, self._on_load_fail)
                return
            self.root.after(0, lambda: self._on_load_ok(j["data"]))
        threading.Thread(target=_worker, daemon=True).start()

    def _on_load_fail(self):
        self._set_offline()
        self.board.set_data([])
        self._update_page_label()
        self._schedule_data_refresh()

    def _on_load_ok(self, orders):
        self._set_online()
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
        self._data_refresh_job = self.root.after(
            REFRESH_SEC * 1000, self._load_orders)

    def _schedule_page_flip(self):
        if self._page_flip_job:
            self.root.after_cancel(self._page_flip_job)
        self._page_flip_job = self.root.after(
            PAGE_FLIP_SEC * 1000, self._flip_page)

    def _flip_page(self):
        flipped = self.board.next_page()
        self._update_page_label()
        if flipped:
            self._schedule_page_flip()
        else:
            self._page_flip_job = self.root.after(2000, self._flip_page)

    def _update_page_label(self):
        total = len(self.board.pages)
        curr  = self.board.current_page + 1
        self.page_lbl.config(
            text="" if total <= 1 else f"PAGE {curr}/{total}")

    # ══════════════════════════════════════════════════════
    #  STATUS + CLOCK
    # ══════════════════════════════════════════════════════
    def _set_online(self):
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 11, 11, fill=GREEN, outline="")
        self.status_lbl.config(text="ONLINE", fg=GREEN)

    def _set_offline(self):
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 11, 11, fill=RED, outline="")
        self.status_lbl.config(text="OFFLINE", fg=RED)
        self.cnt_lbl.config(text="")

    def _tick_clock(self):
        now   = datetime.now()
        hari  = HARI_INDO[now.weekday()]
        bulan = BULAN_INDO[now.month - 1]
        try:
            self.clock_lbl.config(text=now.strftime("%H:%M:%S"))
            self.date_lbl.config(
                text=f"{hari}, {now.day} {bulan} {now.year}")
        except tk.TclError:
            pass
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

    root   = tk.Tk()
    root.withdraw()
    splash = SplashScreen(root)
    root.update()
    AzzahraBoard(root, splash)
    root.deiconify()
    root.mainloop()