"""Страница за семејството: ги чита зачуваните повици."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from database import napravi_tabeli, zemi_korisnik, zemi_povici

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
FAJLOVI = {
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
}
KORISNIK = 1

class Semejstvo(BaseHTTPRequestHandler):
    def _prati(self, telo, tip):
        self.send_response(200)
        self.send_header("Content-Type", tip)
        self.send_header("Content-Length", str(len(telo)))
        self.end_headers()
        self.wfile.write(telo)

    def do_GET(self):
        if self.path.startswith("/povici"):
            napravi_tabeli()
            profil = zemi_korisnik(KORISNIK) or {}
            telo = json.dumps({
                "ime": profil.get("ime", ""),
                "povici": zemi_povici(KORISNIK),
            }, ensure_ascii=False).encode("utf-8")
            self._prati(telo, "application/json; charset=utf-8")
            return
        ime = "index.html" if self.path in ("/", "/index.html") else Path(self.path).name
        if ime in FAJLOVI:
            self._prati((FRONTEND / ime).read_bytes(), FAJLOVI[ime])
            return
        self.send_error(404)

if __name__ == "__main__":
    print("Семејството: http://127.0.0.1:8001")
    ThreadingHTTPServer(("127.0.0.1", 8001), Semejstvo).serve_forever()
