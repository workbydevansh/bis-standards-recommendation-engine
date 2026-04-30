"""Local API and static React demo server for the BIS recommendation engine."""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from src.retriever import load_retriever


ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
RETRIEVER = load_retriever()


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            results, latency = RETRIEVER.recommend(query, top_k=5)
            self._send_json(
                {"query": query, "latency_seconds": round(latency, 4), "results": results}
            )
            return

        self._serve_frontend(parsed.path)

    def _serve_frontend(self, request_path: str) -> None:
        if not FRONTEND_DIST.exists():
            self._send_json(
                {
                    "error": "frontend build missing",
                    "run": "cd frontend && npm install && npm run build",
                },
                status=503,
            )
            return

        relative = unquote(request_path).lstrip("/")
        candidate = (FRONTEND_DIST / relative).resolve() if relative else None
        dist_root = FRONTEND_DIST.resolve()

        if candidate and candidate.is_file() and dist_root in candidate.parents:
            self._send_file(candidate)
            return

        self._send_file(FRONTEND_DIST / "index.html")

    def _send_file(self, path: Path) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        if path.suffix in {".js", ".css", ".svg", ".png", ".ico"}:
            self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Demo running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
