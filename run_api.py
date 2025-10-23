"""
API startup script - ensures correct Python path.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
os.environ['PYTHONPATH'] = str(src_path)

# Now import and run
if __name__ == "__main__":
    import uvicorn

    print("Starting RAG Document Search API...")
    print(f"API docs will be available at: http://localhost:8000/docs")
    print(f"Python path: {src_path}")
    print()

    uvicorn.run(
        "api.main:app",  # Import string instead of object
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
