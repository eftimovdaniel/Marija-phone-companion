import base64
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import urllib.request
from dotenv import load_dotenv
from database import napravi_tabeli, zemi_korisnik, posledni_beleski, zachuvaj_povik
from glas import teksto_vo_govor
from mozok import Marija
from slushaj import govor_vo_tekst

load_dotenv()
PAPKA = os.path.dirname(__file__)
POVIKI = {}

def javna():
    return os.getenv("JAVNA_ADRESA", "").strip().rstrip("/")

def snimi_mp3(ime, tekst):
    pateka = os.path.join(PAPKA, ime)
    teksto_vo_govor(tekst, pateka)
    return f"{javna()}/{ime}"

def twiml(play_url, kraj=False):
    if kraj:
        return f"<Response><Play>{play_url}</Play><Hangup/></Response>"
    return (
        f"<Response><Play>{play_url}</Play>"
        f"<Record action=\"{javna()}/odgovor\" method=\"POST\" maxLength=\"8\" playBeep=\"true\" timeout=\"2\"/>"
        f"</Response>"
    )

def nova_marija():
    napravi_tabeli()
    profil = zemi_korisnik(1)
    if not profil:
        raise SystemExit("Нема корисник со id 1. Прво стартувај test_baza.py")
    return Marija(profil, "утрински", posledni_beleski(1))

def simni(url, pateka):
    if not url.endswith(".mp3"):
        url = url + ".mp3"
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    baranje = urllib.request.Request(url)
    kluc = base64.b64encode(f"{sid}:{token}".encode()).decode()
    baranje.add_header("Authorization", f"Basic {kluc}")
    with urllib.request.urlopen(baranje, timeout=30) as r:
        telo = r.read()
    with open(pateka, "wb") as f:
        f.write(telo)

class Linija(BaseHTTPRequestHandler):
    def _form(self):
        n = int(self.headers.get("Content-Length", 0))
        telo = self.rfile.read(n).decode("utf-8") if n else ""
        return parse_qs(telo)

    def _xml(self, tekst):
        telo = tekst.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(telo)))
        self.end_headers()
        self.wfile.write(telo)

    def do_GET(self):
        ime = os.path.basename(urlparse(self.path).path)
        pateka = os.path.join(PAPKA, ime)
        if ime.endswith(".mp3") and os.path.isfile(pateka):
            with open(pateka, "rb") as f:
                telo = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(telo)))
            self.end_headers()
            self.wfile.write(telo)
            return
        self.send_error(404)

    def do_POST(self):
        pateka = urlparse(self.path).path
        form = self._form()
        call_sid = form.get("CallSid", ["povik"])[0]
        if pateka == "/povik":
            marija = nova_marija()
            POVIKI[call_sid] = marija
            tekst = marija.pozdrav()
            print("Марија:", tekst)
            self._xml(twiml(snimi_mp3(f"pozdrav-{call_sid}.mp3", tekst)))
            return
        if pateka == "/odgovor":
            marija = POVIKI.get(call_sid) or nova_marija()
            POVIKI[call_sid] = marija
            rec = form.get("RecordingUrl", [""])[0]
            if not rec:
                self._xml(twiml(snimi_mp3(f"pak-{call_sid}.mp3", "Не ве слушнав. Кажете уште еднаш.")))
                return
            lokalno = os.path.join(PAPKA, f"snimka-{call_sid}.mp3")
            simni(rec, lokalno)
            tekst = (govor_vo_tekst(lokalno) or "").strip()
            print("Слушнато:", tekst)
            if not tekst:
                self._xml(twiml(snimi_mp3(f"pak-{call_sid}.mp3", "Не ве слушнав. Кажете уште еднаш.")))
                return
            if "крај" in tekst.lower():
                self._xml(twiml(snimi_mp3(f"kraj-{call_sid}.mp3", "Во ред. Пријатен ден."), kraj=True))
                return
            odgovor = marija.odgovori(tekst)
            print("Марија:", odgovor)
            self._xml(twiml(snimi_mp3(f"odgovor-{call_sid}.mp3", odgovor)))
            return
        self.send_error(404)

if __name__ == "__main__":
    print("Линијата слуша на порт 8000")
    ThreadingHTTPServer(("0.0.0.0", 8000), Linija).serve_forever()