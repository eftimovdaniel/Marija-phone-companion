import logging
import os
import re
import time
from dotenv import load_dotenv
from groq import Groq, GroqError
from izvesti import izvesti_semejstvo
from prompts import napravi_sistemski_prompt

load_dotenv()
log = logging.getLogger("marija")
MODEL = os.getenv("MARIJA_MODEL", "openai/gpt-oss-120b")
MAX_PORAKI = 20
MAX_TOKENI = 400
TIMEOUT_SEKUNDI = 15
OBIDI = 2
REZERVEN_ODGOVOR = "Извинете, малку лошо ве слушам. Може ли да повторите?"

ITNI_ZBOROVI = [r"\bпадн", r"\bне можам да станам", r"\bгради(те)?\b", r"\bстега", r"\bне можам да дишам", r"\bтешко дишам", r"\bвртоглав", r"\bми се врти", r"\bкрвар", r"\bонесвест",
    r"\bбрза помош", r"\bмногу лошо",]

IZMAMA_ZBOROVI = [r"\bнаград",r"\bзадржан",r"\bпин\b",r"\bкартичк",r"\bлозинк",r"\bуплат",r"\bпрати пари",r"\bитно плаќ",]

EMODZI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]")
MARKDOWN = re.compile(r"[*#_`>|]")

def najdi(zborovi, tekst):
    tekst = tekst.lower()
    return any(re.search(z, tekst) for z in zborovi)
def ischisti_za_govor(tekst):
    tekst = EMODZI.sub("", tekst)
    tekst = MARKDOWN.sub("", tekst)
    return re.sub(r"\s+", " ", tekst).strip()
class Marija:
    def __init__(self, profil, tip_na_povik="утрински", beleski=""):
        self.client = Groq(timeout=TIMEOUT_SEKUNDI, max_retries=OBIDI)
        self.profil = profil
        self.ime = profil["ime"]
        self.sistem = {
            "role": "system",
            "content": napravi_sistemski_prompt(profil, tip_na_povik, beleski),
        }
        self.istorija = []
        self.nastani = []
        self.izvesteni_tipovi = set()
        self.vkupno_tokeni = 0
    def _poraki_za_ai(self):
        return [self.sistem] + self.istorija[-MAX_PORAKI:]
    def _zapishi_nastan(self, tip, tekst):
        self.nastani.append({
            "tip": tip,
            "tekst": tekst,
            "vreme": time.strftime("%H:%M:%S"),
        })
        log.warning("Nastan: %s - %s", tip, tekst)
    def _izvesti_ednash(self, tip, tekst):
        if tip in self.izvesteni_tipovi:
            return
        self.izvesteni_tipovi.add(tip)
        try:
            izvesti_semejstvo(self.profil, tip, tekst)
        except Exception as greska:
            log.error("Izvestuvanjeto ne uspea: %s", greska)
    def _prasaj_ai(self):
        pocetok = time.time()
        try:
            opcii = {}
            if "gpt-oss" in MODEL:
                opcii["reasoning_effort"] = "low"
            odgovor = self.client.chat.completions.create(
                model=MODEL,
                messages=self._poraki_za_ai(),
                temperature=0.7,
                max_tokens=MAX_TOKENI, **opcii,)
            tekst = ischisti_za_govor(odgovor.choices[0].message.content or "")
            if odgovor.usage:
                self.vkupno_tokeni += odgovor.usage.total_tokens
        except GroqError as greska:
            log.error("Nastanata greska na stranata na GROQ: %s", greska)
            tekst = ""
        if not tekst:
            tekst = REZERVEN_ODGOVOR
        log.info("Odgovor za %.1f sekundi", time.time() - pocetok)
        self.istorija.append({"role": "assistant", "content": tekst})
        return tekst
    def pozdrav(self):
        self.istorija.append({
            "role": "user",
            "content": "[Повикот започна. Ти ѕвониш, таа крена слушалка. Поздрави ја по име, кажи кој си, и прашај што ја мачи. Не спомнувај лекови ниту притисок.]",
        })
        return self._prasaj_ai()
    def odgovori(self, poraka):
        poraka = (poraka or "").strip()
        if not poraka:
            return f"Ало, {self.ime}, дали ме слушате?"
        if najdi(ITNI_ZBOROVI, poraka):
            self._zapishi_nastan("ИТНО", poraka)
            self._izvesti_ednash("ИТНО", poraka)
            self.istorija.append({
                "role": "user",
                "content": (
                    f"{poraka}\n"
                    "[СИСТЕМ: Ова е ИТЕН СЛУЧАЈ. Следи ги правилата за итни случаи: "
                    "194 / сосед, извести семејство, не смирувај со „ништо не е“.]"
                ),
            })
        elif najdi(IZMAMA_ZBOROVI, poraka):
            self._zapishi_nastan("ИЗМАМА", poraka)
            self._izvesti_ednash("ИЗМАМА", poraka)
            self.istorija.append({
                "role": "user",
                "content": (
                    f"{poraka}\n"
                    "[СИСТЕМ: Можно е измама. Предупреди ја, да не дава пари/PIN, "
                    "и кажи дека ќе го споменеш кај семејството.]"
                ),
            })
        else:
            self.istorija.append({"role": "user", "content": poraka})
        return self._prasaj_ai()
    @property
    def ima_itno(self):
        return any(n["tip"] == "ИТНО" for n in self.nastani)
    def napravi_rezime(self):
        if not self.istorija:
            return "Немаше разговор на овој повик."
        nastani_tekst = ""
        if self.nastani:
            delovi = [f"- {n['tip']}: {n['tekst']}" for n in self.nastani]
            nastani_tekst = "Забележани настани:\n" + "\n".join(delovi) + "\n"
        poraki = self._poraki_za_ai() + [
            {
                "role": "user",
                "content": (
                    "Направи кратко резиме за семејството на македонски, 3 до 5 реченици.\n"
                    "Вклучи: расположение, здравје, лекови (дали ги спомна / испила), важни теми.\n"
                    "Ако има ИТНО или ИЗМАМА, тоа стави го на ПОЧЕТОК, јасно и кратко.\n"
                    "Без емоџиња, без наслови. Само резимето.\n"
                    f"{nastani_tekst}"
                ),
            }
        ]
        try:
            opcii = {}
            if "gpt-oss" in MODEL:
                opcii["reasoning_effort"] = "low"
            odgovor = self.client.chat.completions.create(
                model=MODEL,
                messages=poraki,
                temperature=0.3,
                max_tokens=250,**opcii,
            )
            tekst = (odgovor.choices[0].message.content or "").strip()
            if odgovor.usage:
                self.vkupno_tokeni += odgovor.usage.total_tokens
            if tekst:
                return tekst
        except GroqError as greska:
            log.error("Rezimeto ne uspea: %s", greska)
        if self.ima_itno:
            return "ВНИМАНИЕ: за време на повикот имаше итен случај. Прегледајте го разговорот."
        if self.nastani:
            return "Имаше важни настани на повикот. Прегледајте го разговорот."
        return "Резимето не можеше да се направи автоматски."