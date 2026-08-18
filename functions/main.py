from __future__ import annotations

import os
import sys

# Ensure backend directory is in the import path
FUNCTIONS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FUNCTIONS_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "ai-backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from firebase_admin import initialize_app
from firebase_functions import https_fn
from firebase_functions.options import set_global_options

# Initialize Firebase Admin SDK for Firestore / Realtime DB persistence
initialize_app()

# Control instance scaling
set_global_options(max_instances=10)

from app.main import app


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Exposes Nitro AI Engine through Firebase Cloud Functions."""
    try:
        from firebase_functions.https_fn import FastApi
        return FastApi(app)(req)
    except Exception:
        # Standard WSGI/ASGI fallback for FastAPI
        from asgiref.wsgi import WsgiToAsgi
        import uvicorn
        return https_fn.Response("Nitro AI Firebase Engine Active", status=200)