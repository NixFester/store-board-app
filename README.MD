# store-board-app

A lightweight, daylight-optimized kiosk application designed for service centers, repair shops, or any storefront that needs to display a customer queue/task board. Built with Python and Tkinter, it runs flawlessly on slow hardware in fullscreen kiosk mode.

It features a customizable branding header, an auto-paginating service table, a cycling promotional image panel, and a **built-in auto-updater** to keep all your kiosks running the latest version without manual intervention.

---

## ✨ Features

- **Customizable Branding:** Display your store name, tagline, website, and contact number.
- **Dynamic Image Cycling:** Automatically loads and cycles through any images placed in the `assets/` folder.
- **Auto-Pagination:** Table automatically flips through pages of customer data every 8 seconds.
- **RFID Ready:** Hidden RFID input field that silently processes scans and shows toast notifications.
- **Kiosk Mode:** Fullscreen, borderless, and impossible for users to accidentally close.
- **Auto-Updating:** Seamlessly updates itself from GitHub Releases or a static website ZIP file.
- **Daylight Optimized:** Light theme and high-contrast text designed for displays in bright environments.

---

## 📁 Project Structure

```text
store-board-app/
├── main.py              # Main application source code
├── version.txt          # Current application version (e.g., 1.0.0)
├── requirements.txt     # Python dependencies
├── build.bat            # Windows build script (PyInstaller)
├── README.md            # This file
└── assets/              # Create this folder and add your media
    ├── logo.jpg         # Your store logo (square format recommended)
    ├── promo1.jpg       # Promotional images (any aspect ratio)
    ├── promo2.jpg       # Add as many as you want, they cycle automatically
    └── ...
```

---

## ⚙️ Configuration (Making it Yours)

The "Azzahra Computer" branding is just an example. To customize the app for your store, open `main.py` and edit the **CONFIG** section at the top:

```python
# ── Branding ──────────────────────────────────────────────
STORE_NAME    = "YOUR STORE NAME"
FLAVOR_TEXT   = "Your Tagline Here"
WEBSITE_URL   = "https://your-website.com/"
WEBSITE_SHORT = "your-website.com"
CONTACT_NUM   = "+1 555-123-4567"

# ── API ───────────────────────────────────────────────────
API_URL       = "https://your-website.com/api.php" # Your backend API
```

*Note: The app expects your API to return JSON with `success`, `data` (array of orders), `nama_customer`, `keluhan`, `status_order`, and `hari_menunggu` fields.*

---

## 🖼️ Setting Up Assets

1. Create a folder named `assets` in the same directory as `main.py`.
2. Add your logo and name it exactly `logo.jpg`.
3. Add any promotional images you want to display on the right side of the screen (e.g., `promo1.jpg`, `service_ad.png`).
4. The app will automatically scan this folder, ignore `logo.jpg`, and cycle through all other valid image files (`.jpg`, `.png`, `.gif`, etc.) every 6 seconds.

---

## 🚀 Building the Application

To compile the app into a standalone `.exe`:

1. Ensure Python is installed on your build machine.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the build script:
   ```batch
   build.bat
   ```
4. Your compiled app and a `dist.zip` will be located in:
   ```text
   dist/store-board-app/store-board-app.exe
   dist/store-board-app/dist.zip
   ```

---

## 🔄 Auto-Update System

This app can automatically check for updates, download them in the background, and restart itself with the new version. You can choose between **GitHub Releases** (Recommended) or a **Website Hosted ZIP**.

Configure this in the `Auto-Update Config` section of `main.py`:
```python
UPDATE_METHOD         = "github" # "github" or "website"
```

### Option A: GitHub Releases (Recommended)
Best for tracking versions, release notes, and leveraging GitHub's fast CDN.

1. Create a GitHub repository for your app.
2. In `main.py`, set your GitHub details:
   ```python
   GITHUB_OWNER = "your-github-username"
   GITHUB_REPO  = "store-board-app"
   ```
3. **To publish an update:**
   - Increment the version number in `version.txt` (e.g., from `1.0.0` to `1.0.1`).
   - Run `build.bat` to generate the new `dist.zip`.
   - Go to your GitHub repo -> Releases -> Draft a new release.
   - Set the Tag to match the version (e.g., `v1.0.1`).
   - Upload the new `dist.zip` as an asset.
   - Publish the release.

### Option B: Website Hosted ZIP
Best if you want to host the files on your own server.

1. In `main.py`, set:
   ```python
   UPDATE_METHOD      = "website"
   WEBSITE_VERSION_URL = "https://your-website.com/version.txt"
   WEBSITE_DIST_URL    = "https://your-website.com/dist.zip"
   ```
2. **To publish an update:**
   - Increment the version number in `version.txt`.
   - Run `build.bat`.
   - Upload the new `version.txt` to your server (overwriting the old one). The file should *only* contain the version number (e.g., `1.0.1`).
   - Upload the new `dist.zip` to your server (overwriting the old one).

### How the Update Process Works
1. The app checks for updates 15 seconds after startup, and every 30 minutes thereafter.
2. If a newer version is found, it downloads `dist.zip` to a temporary folder.
3. It extracts the ZIP and generates a hidden `updater.bat` script.
4. The app displays a toast notification ("Update ready — restarting…") and then exits.
5. `updater.bat` waits 3 seconds, copies the new files over the old ones, restarts `store-board-app.exe`, and deletes itself.

---

## ⌨️ Keyboard Shortcuts

Since the app runs in borderless fullscreen mode, these shortcuts are essential for maintenance:

| Key | Action |
|-----|--------|
| `Esc` | Exit the application |
| `Ctrl` + `U` | Manually trigger an update check |

---

## 🖥️ Screen Layout Preview

```text
┌──────────────────────────────────────────────────────────────┐
│ [LOGO] YOUR STORE NAME                    12:34:56            │
│        Your Tagline Here                Mon, 15 Jan 2025     │
│        your-website.com                                      │
│        +1 555-123-4567                                       │
├────────────────────────────────┬─────────────────────────────┤
│ NO│CUSTOMER│KELUHAN│STATUS│WAIT│                             │
│───┼────────┼───────┼──────┼────│   ┌─────────────────────┐  │
│ 01│...     │...    │BARU  │TODY│   │                     │  │
│ 02│...     │...    │PROSES│2H  │   │  [Cycling Promos]   │  │
│ 03│...     │...    │BARU  │TODY│   │                     │  │
│   │        │       │      │    │   └─────────────────────┘  │
│   │        │       │      │    │      ● ● ○ ○ ○             │
│   │        │       │      │    │  ─────────────────────     │
│   │        │       │      │    │  🌐 your-website.com       │
│   │        │       │      │    │  📞 +1 555-123-4567        │
├────────────────────────────────┴─────────────────────────────┤
│ ● ONLINE  BARU 3 · DIPROSES 5  PAGE 1/2    v1.0.1 up to date │
└──────────────────────────────────────────────────────────────┘
```