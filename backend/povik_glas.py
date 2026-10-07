import logging
import os
import subprocess
import sys
from database import napravi_tabeli, zemi_korisnik, posledni_beleski, zachuvaj_povik
from glas import teksto_vo_govor
from izvesti import izvesti_semejstvo
from mozok import Marija
from slushaj import snimi, govor_vo_tekst

logging.basicConfig(level=logging.INFO, format="   [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)

def kazhi(tekst):
    pateka = os.path.join(os.path.dirname(__file__),"odgovor.mp3")
    teksto_vo_govor(tekst, pateka)
    subprocess.run(["afplay", pateka], check=False)
def slushaj():
    pateka = os.path.join(os.path.dirname(__file__),"snimka.wav")
    snimi(pateka)
    tekst = (govor_vo_tekst(pateka) or "").strip()
    print ("Слушнато:", tekst)
    return tekst
korisnik_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
tip = sys.argv[2] if len(sys.argv) > 2 else "утрински"
napravi_tabeli()
profil = zemi_korisnik(korisnik_id)
if not profil:
    sys.exit(f"Нема корисник со id {korisnik_id}. Прво стартувај test_baza.py")
beleski = posledni_beleski(korisnik_id)
marija = Marija(profil, tip, beleski)
print(f"\n--- Марија зборува со {profil['ime']}. Кажи „крај“ за крај ---\n")
kazhi(marija.pozdrav())
while True:
    try:
        poraka = slushaj()
    except KeyboardInterrupt:
        break
    if not poraka:
        continue
    if "Крај" in poraka.lower():
        break
    kazhi(marija.odgovori(poraka))
print("\n--- Повикот заврши. Правам резиме... ---")
rezime = ""
try:
    rezime = marija.napravi_rezime()
except Exception as greska:
    if marija.ima_itno:
        rezime = "ВНИМАНИЕ: за време на повикот имаше итен случај. Прегледајте го разговорот."
    elif marija.nastani:
        rezime = "Имаше важни настани на повикот. Прегледајте го разговорот."
    else:
        rezime = "Резимето не можеше да се направи автоматски."
povik_id = zachuvaj_povik(korisnik_id, tip, marija, rezime)
print(f"\nРЕЗИМЕ ЗА СЕМЕЈСТВОТО:\n{rezime}")
print(f"Повикот е зачуван во базата (id {povik_id}).")
if marija.nastani:
    izvesti_semejstvo(profil, "РЕЗИМЕ", rezime, rezime)