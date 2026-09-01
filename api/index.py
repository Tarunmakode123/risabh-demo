import sys
import os

# Add root directory to sys.path for Vercel imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Export ASGI app for Vercel Serverless Function
