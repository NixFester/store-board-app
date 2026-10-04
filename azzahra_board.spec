# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []

# Collect all PIL/Pillow sub-modules so image loading works correctly
hiddenimports = []
tmp_ret = collect_all('PIL')
datas    += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Modules our app explicitly uses that PyInstaller may miss
hiddenimports += [
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.cookies',
    'requests.exceptions',
    'requests.models',
    'requests.sessions',
    'requests.structures',
    'requests.utils',
    'urllib3',
    'urllib3.util',
    'urllib3.util.retry',
    'certifi',
    'charset_normalizer',
    'idna',
    'tkinter',
    'tkinter.ttk',
    'json',
    'threading',
    'zipfile',
    'shutil',
    'subprocess',
    'glob',
    'tempfile',
]

# ── Modules to exclude ────────────────────────────────────────────────────────
# Suppresses the PyInstaller "missing module" warnings for things we don't need.
excludes = [
    # ── Unix / macOS platform modules (not available on Windows) ──────────────
    'fcntl', 'grp', 'pwd', 'posix', 'resource', 'termios',
    '_posixshmem', '_posixsubprocess', '_scproxy',
    'readline', 'rlcompleter',

    # ── Frozen-interpreter internals (PyInstaller false positives) ────────────
    '_frozen_importlib', '_frozen_importlib_external',

    # ── Site customisation stubs (not present in frozen builds) ───────────────
    'usercustomize', 'sitecustomize',

    # ── JVM / VMS platform modules (not applicable) ───────────────────────────
    'java', 'java.lang', 'vms_lib',

    # ── Linux-specific ABI helpers ────────────────────────────────────────────
    '_manylinux',

    # ── Optional HTTP extras we do not use ────────────────────────────────────
    'brotli',
    'h2', 'h2.connection', 'h2.events',
    'OpenSSL', 'OpenSSL.crypto',
    'cryptography', 'cryptography.x509', 'cryptography.x509.UnsupportedExtension',
    'cryptography.hazmat',
    'bcrypt',
    'socks',
    'simplejson',
    'chardet',

    # ── Emscripten / Pyodide (WebAssembly, not applicable) ───────────────────
    'pyodide', 'pyodide.ffi', 'js',

    # ── PIL optional extras we don't need ─────────────────────────────────────
    'olefile',          # FPX/MIC image formats
    'PIL.ImageQt',      # Qt integration

    # ── NumPy — pulled in by PIL hooks but NOT used by this app ──────────────
    'numpy',
    'numpy.core',
    'numpy._core',
    'numpy.linalg',
    'numpy.fft',
    'numpy.random',
    'numpy.polynomial',
    'numpy.lib',
    'numpy.testing',
    'numpy._distributor_init_local',
    'numpy._distributor_init',

    # ── YAML — not used by this app ───────────────────────────────────────────
    'yaml',

    # ── XML-RPC extras ────────────────────────────────────────────────────────
    'xmlrpclib',
    'defusedxml',
    'defusedxml.xmlrpc',

    # ── Setuptools / packaging internals (not needed at runtime) ─────────────
    'setuptools',
    'pkg_resources',
    'distutils',

    # ── Async / multiprocessing APIs not used ─────────────────────────────────
    'asyncio',
    'multiprocessing',

    # ── Misc optional deps referenced by urllib3 / requests ──────────────────
    'importlib_resources',
    'trove_classifiers',
    'threadpoolctl',
    'win32pdh',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='azzahra_board',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='azzahra_board',
    # Keep all DLLs (including python314.dll) next to the .exe instead of
    # inside the _internal/ subdirectory that PyInstaller 6+ creates by default.
    # This prevents the "python3xx.dll could not be found" error.
    contents_directory='.',
)
