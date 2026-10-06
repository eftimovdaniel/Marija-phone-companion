import os
import subprocess
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
MODEL = "whisper-large-v3"
PROMPT = "Здраво, како си денес?"

def snimi(pateka, sekundi=8):
    print(f"Зборувај {sekundi} секунди...")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "avfoundation", "-i", ":1",
         "-t", str(sekundi), "-ar", "16000", "-ac", "1", pateka],
        check=True,
    )

def govor_vo_tekst(pateka):
    klient = Groq()
    with open(pateka, "rb") as f:
        odgovor = klient.audio.transcriptions.create(
            file=f,
            model=MODEL,
            language="mk",
            temperature=0,
            prompt=PROMPT,
        )
    return odgovor.text

if __name__ == "__main__":
    pateka = os.path.join(os.path.dirname(__file__), "snimka.wav")
    snimi(pateka)
    print("Текст од говорот:", govor_vo_tekst(pateka))