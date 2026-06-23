# hook_fix_requests.py
# PyInstaller runtime hook — runs before app.py starts.
# Fixes: requests can't find certifi's cacert.pem when frozen.

import os
import sys

# When frozen, sys._MEIPASS is the bundle's temp/extract folder.
# We point SSL_CERT_FILE + REQUESTS_CA_BUNDLE at the bundled cert so
# requests doesn't try to load from the original Python install path.
if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS
    cert_path = os.path.join(bundle_dir, "certifi", "cacert.pem")
    if os.path.isfile(cert_path):
        os.environ["SSL_CERT_FILE"]      = cert_path
        os.environ["REQUESTS_CA_BUNDLE"] = cert_path
