from firebase_admin import initialize_app
from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from fastapi import FastAPI

# Initialize Firebase Admin
initialize_app()

# Set global options for cost/instance control
set_global_options(max_instances=10)

# Create your FastAPI app
app = FastAPI()


@app.get("/")
def read_root():
  return {"message": "Welcome to Nitro Decoupled AI API!"}


@app.get("/nitro-ai")
def run_nitro_ai():
  # Add your logic here for your 16-AI model aggregator
  return {"status": "success", "model": "Nitro 16-in-1 AI active"}


# Expose FastAPI as a single Firebase Cloud Function named 'api'
@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
  return a(req)  # Let FastAPI handle the request routing