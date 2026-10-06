import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
DB_PATEKA = Path(__file__).parent / "database.db"
@contextmanager
def baza():
    kon = sqlite3.connect(DB_PATEKA)
    kon.row_factory = sqlite3.Row
    try:
        yield kon
        kon.commit()
    finally:
        kon.close()
def napravi_tabeli():
    with baza() as kon:
        kon.executescript ("""
            CREATE TABLE IF NOT EXISTS korisnici (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ime         TEXT NOT NULL,
                godini      INTEGER,
                grad        TEXT,
                telefon     TEXT UNIQUE,
                semejstvo   TEXT,
                semejstvo_telefon TEXT,
                semejstvo_email   TEXT,
                lekovi      TEXT,
                interesi    TEXT,
                obrakjanje  TEXT DEFAULT 'Вие',
                kreiran     TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS povici (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                korisnik_id  INTEGER NOT NULL REFERENCES korisnici(id),
                pocetok      TEXT NOT NULL,
                tip          TEXT,
                razgovor     TEXT,              -- целиот разговор како JSON
                nastani      TEXT,              -- итни случаи, измами, здравје (JSON)
                itno         INTEGER DEFAULT 0, -- 1 ако имало итен случај
                rezime       TEXT,              -- кратко резиме за семејството
                tokeni       INTEGER DEFAULT 0
            );
        """)
        koloni = {red[1] for red in kon.execute("PRAGMA table_info(korisnici)")}
        if "semejstvo_telefon" not in koloni:
            kon.execute("ALTER TABLE korisnici ADD COLUMN semejstvo_telefon TEXT")
        if "semejstvo_email" not in koloni:
            kon.execute("ALTER TABLE korisnici ADD COLUMN semejstvo_email TEXT")
def dodaj_korisnik(profil):
    with baza () as kon:
        kursor = kon.execute(
              """INSERT INTO korisnici
               (ime, godini, grad, telefon, semejstvo, lekovi, interesi, obrakjanje,
                semejstvo_telefon, semejstvo_email)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profil["ime"], profil.get("godini"), profil.get("grad"),
                profil.get("telefon"), profil.get("semejstvo"), profil.get("lekovi"),
                profil.get("interesi"), profil.get("obrakjanje", "Вие"),
                profil.get("semejstvo_telefon"), profil.get("semejstvo_email"),
            ),
        )
        return kursor.lastrowid
def azuriraj_kontakt_semejstvo(korisnik_id, telefon=None, email=None):
    with baza() as kon:
        if telefon is not None:
            kon.execute(
                "UPDATE korisnici SET semejstvo_telefon = ? WHERE id = ?",
                (telefon, korisnik_id),
            )
        if email is not None:
            kon.execute(
                "UPDATE korisnici SET semejstvo_email = ? WHERE id = ?",
                (email, korisnik_id),
            )
def zemi_korisnik(korisnik_id):
    with baza() as kon:
        red = kon.execute("SELECT * FROM korisnici WHERE id = ?", (korisnik_id,)).fetchone()
        return dict(red) if red else None
def zemi_korisnik_po_telefon(telefon):
    with baza() as kon:
        red = kon.execute("SELECT * FROM korisnici WHERE telefon = ?", (telefon,)).fetchone()
        return dict(red) if red else None
def zachuvaj_povik(korisnik_id, tip, marija, rezime=""):
    with baza() as kon:
        kursor = kon.execute(
              """INSERT INTO povici
               (korisnik_id, pocetok, tip, razgovor, nastani, itno, rezime, tokeni)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                korisnik_id,
                datetime.now().isoformat(timespec="seconds"),
                tip,
                json.dumps(marija.istorija, ensure_ascii=False),  # ensure_ascii=False = кирилица останува читлива
                json.dumps(marija.nastani, ensure_ascii=False),
                1 if marija.ima_itno else 0,
                rezime,
                marija.vkupno_tokeni,
            ),
        )
        return kursor.lastrowid
def posledni_beleski(korisnik_id, broj = 3):
    with baza() as kon:
        redovi = kon.execute (
           """SELECT pocetok, tip, rezime FROM povici
               WHERE korisnik_id = ? AND rezime != ''
               ORDER BY pocetok DESC LIMIT ?""",(korisnik_id, broj), 
        ).fetchall()

        return "\n".join(
        f"{r['pocetok'][:10]} ({r['tip']}): {r['rezime']}" for r in reversed(redovi))