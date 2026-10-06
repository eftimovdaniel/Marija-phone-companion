import asyncio
import os
import subprocess
import sys
import edge_tts

GLAS = "mk-MK-MarijaNeural"
POZDRAV = "Добро утро, Верка! Јас сум Марија. Како спиевте синоќа?"

async def _snimi(tekst, pateka):
    await edge_tts.Communicate(tekst,GLAS, rate="-10%").save(pateka)

def teksto_vo_govor(tekst, pateka):
    asyncio.run(_snimi(tekst, pateka))
if __name__ == "__main__":
    tekst = " ".join(sys.argv[1:]) or POZDRAV
    pateka=os.path.join(os.path.dirname(__file__), "pozdrav.mp3")
    teksto_vo_govor(tekst, pateka)
    print (f"Гласот е зачуван во {pateka}.")
    if sys.platform == "darwin":
        subprocess.run(["afplay", pateka],check=False)