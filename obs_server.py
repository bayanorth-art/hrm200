import json
import logging
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from hr_overlay.obs_page import OBS_PAGE_HTML
from hr_overlay.settings import Settings

LOCAL_HOST = "127.0.0.1"

log = logging.getLogger(__name__)


def build_obs_state(snapshot: dict, settings: Settings) -> dict:
    return {
        **snapshot,
        "font_size": settings.overlay_font_size,
        "scale": settings.overlay_scale,
        "opacity": settings.overlay_opacity,
        "text_color": settings.overlay_text_color,
        "heart_color": settings.overlay_heart_color,
        "background": settings.overlay_background,
        "heartbeat": settings.overlay_heartbeat,
    }


class ObsOverlayServer:
    def __init__(self, port: int, state_provider: Callable[[], dict]) -> None:
        self.port = port
        self._state_provider = state_provider
        self._server: ThreadingHTTPServer | None = None

    @property
    def url(self) -> str:
        return f"http://{LOCAL_HOST}:{self.port}/"

    @property
    def running(self) -> bool:
        return self._server is not None

    def start(self) -> bool:
        try:
            self._server = ThreadingHTTPServer((LOCAL_HOST, self.port), _make_handler(self._state_provider))
        except OSError:
            log.exception("Could not start the OBS overlay server on port %s", self.port)
            return False
        threading.Thread(target=self._server.serve_forever, name="obs-overlay", daemon=True).start()
        return True

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


def _make_handler(state_provider: Callable[[], dict]) -> type[BaseHTTPRequestHandler]:
    class OverlayRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._respond(200, "text/html; charset=utf-8", OBS_PAGE_HTML.encode("utf-8"))
            elif path == "/api/state":
                body = json.dumps(state_provider()).encode("utf-8")
                self._respond(200, "application/json", body)
            else:
                self._respond(404, "text/plain; charset=utf-8", b"Not found")

        def _respond(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args) -> None:
            return

    return OverlayRequestHandler
