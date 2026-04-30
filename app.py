"""Local API and static React demo server for the BIS recommendation engine."""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from src.retriever import load_retriever

# Root directory of the project
ROOT = Path(__file__).resolve().parent

# Path where the built React frontend files are stored
FRONTEND_DIST = ROOT / "frontend" / "dist"

# Load the recommendation engine once when the server starts
# This avoids reloading index/model data for every API request
RETRIEVER = load_retriever()


class Handler(BaseHTTPRequestHandler):
    # Handles browser preflight requests for CORS
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()
        
    # Handles all GET requests:
    # 1. API search requests
    # 2. Static frontend file requests
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        
       # API endpoint for recommendation search
        # Example: /api/search?q=white%20cement
        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            
            # Extract query parameter q from the URL
            query = params.get("q", [""])[0]
            # Get top 5 recommended BIS standards and latency
            results, latency = RETRIEVER.recommend(query, top_k=5)
           # Send recommendation results as JSON response
            self._send_json(
                {"query": query, "latency_seconds": round(latency, 4), "results": results}
            )
            return
        # If request is not for API, serve the React frontend
        self._serve_frontend(parsed.path)

    def _serve_frontend(self, request_path: str) -> None:
         # If frontend build does not exist, return helpful setup message
        if not FRONTEND_DIST.exists():
            self._send_json(
                {
                    "error": "frontend build missing",
                    "run": "cd frontend && npm install && npm run build",
                },
                status=503,
            )
            return
        # Convert requested URL path into a file path inside frontend/dist
        relative = unquote(request_path).lstrip("/")
        candidate = (FRONTEND_DIST / relative).resolve() if relative else None
        dist_root = FRONTEND_DIST.resolve()
        
        # Serve requested static file only if it exists inside frontend/dist
        # This prevents accessing files outside the frontend build folder
        if candidate and candidate.is_file() and dist_root in candidate.parents:
            self._send_file(candidate)
            return
        # For React routes, serve index.html so client-side routing works
        self._send_file(FRONTEND_DIST / "index.html")

    # Reads and sends a static file such as HTML, JS, CSS, image, or SVG
    def _send_file(self, path: Path) -> None:
        # Detect file type automatically for browser compatibility
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        # Cache static assets to improve frontend loading speed
        if path.suffix in {".js", ".css", ".svg", ".png", ".ico"}:
            self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(content)
    # Disables default HTTP request logs in the terminal
    def log_message(self, format: str, *args: object) -> None:
        return
    # Sends dictionary data as a JSON API response
    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        
     # Adds CORS headers so frontend can call API from another origin if needed
    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def main() -> None:
     # Start a multi-threaded local HTTP server on localhost port 8000
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
     # Print local demo URL for the user
    print("Demo running at http://127.0.0.1:8000")
    # Keep the server running until manually stopped
    server.serve_forever()


if __name__ == "__main__":
    main()

