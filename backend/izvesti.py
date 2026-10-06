import logging
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
log = logging.getLogger("marija")

def izvesti_semejstvo(profil, tip, tekst, rezime=""):
    naslov, telo = sostavi_izvestuvanje(profil, tip, tekst, rezime)
    prikazi_vo_terminal(naslov, telo)
    isprati_email(profil, naslov, telo)
    isprati_sms(profil, naslov, telo)

def sostavi_izvestuvanje(profil, tip, tekst, rezime=""):
    ime = profil.get("ime") or "корисничката"
    semejstvo = profil.get("semejstvo") or "семејството"
    if tip == "ИТНО":
        naslov = f"ИТНО: {ime}"
        telo = (
            f"{semejstvo}, итен случај кај {ime}.\n"
            f"Што рече: {tekst}\n"
            "Јавете се веднаш."
        )
    elif tip == "ИЗМАМА":
        naslov = f"ИЗМАМА: {ime}"
        telo = (
            f"{semejstvo}, можно е измама кај {ime}.\n"
            f"Што рече: {tekst}\n"
            "Проверете пред да плати или да даде податоци."
        )
    else:
        naslov = f"Резиме од повик: {ime}"
        telo = rezime or tekst or "Нема резиме."
    return naslov, telo

def prikazi_vo_terminal(naslov, telo):
    linija = "=" * 48
    print(f"\n{linija}\nИЗВЕСТУВАЊЕ ДО СЕМЕЈСТВОТО\n{naslov}\n{telo}\n{linija}\n")
    log.warning("Izvestuvanje: %s", naslov)

def isprati_email(profil, naslov, telo):
    primac = (profil.get("semejstvo_email") or "").strip()
    host = os.getenv("SMTP_HOST", "").strip()
    if not primac or not host:
        log.info("Email ne e pusten (nema semejstvo_email ili SMTP_HOST).")
        return
    poraka = EmailMessage()
    poraka["Subject"] = naslov
    poraka["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "marija@localhost"
    poraka["To"] = primac
    poraka.set_content(telo)
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            server.starttls()
        with server:
            user = os.getenv("SMTP_USER", "").strip()
            lozinka = os.getenv("SMTP_PASSWORD", "")
            if user:
                server.login(user, lozinka)
            server.send_message(poraka)
        log.info("Email ispraten do %s", primac)
    except Exception as greska:
        log.error("Email ne uspea: %s", greska)

def isprati_sms(profil, naslov, telo):
    broj = (profil.get("semejstvo_telefon") or "").strip()
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    od = os.getenv("TWILIO_FROM", "").strip()
    if not broj or not sid or not token or not od:
        log.info("SMS ne e pusten (nema semejstvo_telefon ili Twilio klucevi).")
        return
    try:
        from twilio.rest import Client
        Client(sid, token).messages.create(
            body=f"{naslov}\n{telo}",
            from_=od,
            to=broj,
        )
        log.info("SMS ispraten do %s", broj)
    except Exception as greska:
        log.error("SMS ne uspea: %s", greska)
