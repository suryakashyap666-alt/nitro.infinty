import os
import sys

# Ensure ai-backend is in Python path for Vercel / serverless execution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "ai-backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import the unified Nitro AI FastAPI app
from app.main import app

# Serverless ASGI handler
app = app