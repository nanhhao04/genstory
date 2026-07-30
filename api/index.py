import os
import sys

# Ensure the root directory is in python path for Vercel Serverless environment
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.api.main import app  # noqa: E402

__all__ = ["app"]
