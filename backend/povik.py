import logging
import sys
from database import napravi_tabeli, zemi_korisnik, posledni_beleski, zachuvaj_povik
from izvesti import izvesti_semejstvo
from mozok import Marija
logging.basicConfig(level=logging.INFO, format="   [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING) 

korisnik_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
tip = sys.argv[2] if len(sys.argv) > 2 else "утрински"
napravi_tabeli()
profil = zemi_korisnik(korisnik_id)
if not profil:
    sys.exit(f"Нема корисник со id {korisnik_id}. Прво стартувај test_baza.py")
beleski = posledni_beleski(korisnik_id)
print(f"\nБелешки од минатите повици:\n{beleski or '(нема)'}")

marija = Marija(profil, tip, beleski)
print(f"\n--- Марија ѕвони на {profil['ime']} ({tip} повик). Напиши „крај“ за крај ---\n")
print("Марија:", marija.pozdrav(), "\n")
while True:
    try:
        poraka = input(f"{profil['ime']}: ")
    except (KeyboardInterrupt, EOFError):
        break
    if poraka.strip().lower() == "крај":
        break
    print("Марија:", marija.odgovori(poraka), "\n")
print("\n--- Повикот заврши. Правам резиме... ---")
rezime = ""
try:
    rezime = marija.napravi_rezime()
except Exception as greska:
    logging.getLogger("marija").error("Rezimeto padna: %s", greska)
    if marija.ima_itno:
        rezime = "ВНИМАНИЕ: за време на повикот имаше итен случај. Прегледајте го разговорот."
    elif marija.nastani:
        rezime = "Имаше важни настани на повикот. Прегледајте го разговорот."
    else:
        rezime = "Резимето не можеше да се направи автоматски."
povik_id = zachuvaj_povik(korisnik_id, tip, marija, rezime)
print(f"\nРЕЗИМЕ ЗА СЕМЕЈСТВОТО:\n{rezime}")
print(f"\nИтно: {'ДА' if marija.ima_itno else 'не'} | " f"Настани: {len(marija.nastani)} | Токени: {marija.vkupno_tokeni}")
print(f"Повикот е зачуван во базата (id {povik_id}).")
if marija.nastani:
    izvesti_semejstvo(profil, "РЕЗИМЕ", rezime, rezime)