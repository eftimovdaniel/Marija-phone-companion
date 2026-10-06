import logging
from mozok import Marija
logging.basicConfig(level=logging.INFO, format="   [%(levelname)s] %(message)s")

profil = {
    "ime": "Верка",
    "godini": 74,
    "grad": "Битола",
    "semejstvo": "ќерка ѝ Ана",
    "lekovi": "апче за притисок наутро",
    "interesi": "градинарство",
    "obrakjanje": "Вие",
}
marija = Marija(profil, "утрински", "Вчера ја болеше грбот.")
print("\n--- Марија ѕвони... (напиши „крај“ за да заврши) ---\n")
print("Марија:", marija.pozdrav(), "\n")
while True:
    try:
        poraka = input("Верка: ")
    except (KeyboardInterrupt, EOFError):
        break

    if poraka.strip().lower() == "крај":
        break

    print("Марија:", marija.odgovori(poraka), "\n")
print("\n--- Повикот заврши ---")
print("Настани:", marija.nastani if marija.nastani else "нема")
print("Итно:", "ДА" if marija.ima_itno else "не")
print("Потрошени токени:", marija.vkupno_tokeni)