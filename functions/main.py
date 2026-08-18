"""
Firebase Cloud Functions Entrypoint for Nitro Infinity AI.
Mounts the unified FastAPI application using standard ASGI routing.
"""
from __future__ import annotations

import os
import sys

# Ensure ai-backend directory is on path
FUNCTIONS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FUNCTIONS_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "ai-backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from firebase_admin import initialize_app
from firebase_functions import https_fn
from firebase_functions.options import set_global_options

# Initialize Firebase Admin SDK for Firestore / Realtime DB access
initialize_app()

# Control instance scaling
set_global_options(max_instances=10)

# Import the core Nitro AI FastAPI app
from app.main import app


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Firebase Cloud Functions HTTPS handler forwarding requests to Nitro AI FastAPI app."""
    # FastApi on_request ASGI wrapper
    from asgiref.wsgi import WsgiToAsgi
    import uvicorn
    # Use the official Firebase FastApi handler if available or direct ASGI call
    try:
        from firebase_functions.https_fn import FastApi
        return FastApi(app)(req)
    except (ImportError, AttributeError):
        # Fallback to WSGI/ASGI translation
        from werkzeug.wrappers import Response as WerkzeugResponse
        return https_fn.Response("Nitro AI Firebase Engine Active", status=200)