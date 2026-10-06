from database import (napravi_tabeli, dodaj_korisnik, zemi_korisnik, zemi_korisnik_po_telefon, posledni_beleski, azuriraj_kontakt_semejstvo)
napravi_tabeli()
profil = {
    "ime": "Верка",
    "godini": 74,
    "grad": "Битола",
    "telefon": "+38970000000",
    "semejstvo": "ќерка ѝ Ана",
    "semejstvo_telefon": "+38970111222",
    "semejstvo_email": "ana@example.com",
    "lekovi": "апче за притисок наутро",
    "interesi": "градинарство",
    "obrakjanje": "Вие",
}
postoecka = zemi_korisnik_po_telefon(profil["telefon"])
if postoecka: 
    korisnik_id = postoecka["id"]
    print("Verka e pronajdena vo bazata so ID:", korisnik_id)
else:
    korisnik_id = dodaj_korisnik(profil)
    print("Verka e dodadena vo bazata so ID:", korisnik_id)
azuriraj_kontakt_semejstvo(korisnik_id, profil["semejstvo_telefon"], profil["semejstvo_email"])
print ("Profil od bazata: ", zemi_korisnik(korisnik_id))
print ("Beleska: ", posledni_beleski(korisnik_id) or "(ne se napraveni povici)")