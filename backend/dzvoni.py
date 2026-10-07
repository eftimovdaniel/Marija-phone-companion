import os
from twilio.rest import Client
from dotenv import load_dotenv
from glas import teksto_vo_govor
load_dotenv()
POZDRAV =  "Добро утро. Јас сум Марија, компјутерски помошник. Кажете што ве мачи?"

def napravi_pozdrav():
    pateka = os.path.join(os.path.dirname(__file__),"pozdrav.mp3")
    teksto_vo_govor(POZDRAV, pateka)
    return pateka

def dzvoni():
    adresa = os.getenv("JAVNA_ADRESA","").strip().rstrip("/")
    od = os.getenv("TWILIO_FROM","").strip()
    kon = os.getenv("MOJ_TELEFON", "").strip()
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    if not all ([adresa,od,kon,sid,token]):
        raise SystemExit("Пополни ги TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, MOJ_TELEFON и JAVNA_ADRESA во .env")
    napravi_pozdrav()
    klient = Client(sid, token)
    povik = klient.calls.create(to = kon, from_ = od, twiml=f"<Response><Play>{adresa}/pozdrav.mp3</Play></Response>",)
    print ("Повикот е пуштен", povik.sid)
if __name__ == "__main__":
    dzvoni()