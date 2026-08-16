import os
import sys

# Ensure ai-backend is in Python path for Vercel's serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "ai-backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import the FastAPI app instance from your backend
from app.main import app

# Handler for Vercel WSGI/ASGI serverless runner
app = app