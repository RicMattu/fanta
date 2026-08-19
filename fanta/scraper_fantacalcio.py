"""Scraper della pagina 'probabili formazioni' di fantacalcio.it.

Scoperta chiave: la pagina e' resa lato server e, accanto a ogni giocatore,
riporta gia' la percentuale di titolarita'. Quindi:

  - p_start  = percentuale / 100   (gia' corretta per ballottaggi)
  - status   = OUT se squalificato/infortunato, DOUBTFUL se 'in dubbio'
  - exp_vote = NON presente qui (sta nella pagina statistiche/fantamedia):
               per la v1 si lascia il default e si ottimizza sulla titolarita'.

Design del parser: NON dipende da classi CSS (fragili). Lavora sul testo
reso della pagina. In produzione si passa a `parse` o il testo di
`page.inner_text("body")` (Playwright) oppure l'HTML grezzo (verra' ridotto a
testo). Qui sotto la logica e' testata su un estratto reale della pagina.

NOTA rete/ToS: fantacalcio.it puo' bloccare richieste 'requests' semplici e i
suoi Termini di Servizio vanno verificati prima di uno scraping ricorrente.
Il fetch dal vivo (fetch_html) e' separato dal parsing proprio per poterlo
sostituire (requests, httpx, o Playwright) senza toccare la logica.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Role, Status

# --- normalizzazione riga per riga -----------------------------------------

_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")   # [Nome](url) -> Nome
_PCT = re.compile(r"^\s*(\d{1,3})\s*%\s*$")        # riga con solo 'NN%'
_TEAM_HEADER = re.compile(r"^\s*#{3}\s+(.+?)\s*$")  # '### Inter'
_SECTION = re.compile(r"(squalificati|infortunati|in dubbio|diffidati|panchina)", re.I)
_NOISE = re.compile(r"nessun calciatore|presentazione|dettaglio|ballottagg|ultimo aggiornamento", re.I)
_MODULE = re.compile(r"^\s*\d(?:-\d){1,3}\s*$")     # '3-5-2'


def _strip_links(line: str) -> str:
    return _MD_LINK.sub(r"\1", line)


@dataclass
class ProbRecord:
    """Un giocatore come letto dalla pagina probabili."""

    name: str
    team: str
    p_start: float
    status: Status
    is_starter: bool  # True se tra gli 11, False se panchina


def parse(text: str) -> list[ProbRecord]:
    """Estrae i record dalla pagina probabili (testo reso o markdown)."""
    team: str | None = None
    section = "xi"          # 'xi' | 'panca' | 'squalificati' | 'infortunati' | 'dubbio'
    pending_name: str | None = None
    records: dict[tuple[str, str], ProbRecord] = {}
    # nelle sezioni stato salvo la riga intera (nome + eventuale descrizione):
    # la risolvo dopo, per PREFISSO sui nomi realmente presenti, cosi' non
    # dipendo da come sono separati nome e descrizione.
    status_out_lines: list[str] = []
    status_doubt_lines: list[str] = []

    def sec_from(label: str) -> str:
        l = label.lower()
        if "panchina" in l:
            return "panca"
        if "squalificati" in l:
            return "squalificati"
        if "infortunati" in l:
            return "infortunati"
        if "in dubbio" in l:
            return "dubbio"
        return section

    for raw in text.splitlines():
        line = _strip_links(raw).strip()
        if not line:
            continue

        m_team = _TEAM_HEADER.match(raw)
        if m_team:
            team = m_team.group(1).strip()
            section = "xi"
            pending_name = None
            continue

        if _MODULE.match(line):          # riga del modulo, ignorala
            continue

        if _SECTION.search(line) and (line.startswith("#") or line.lower() in
                                      ("panchina", "infortunati") or "infortunati" in line.lower()):
            section = sec_from(line)
            pending_name = None
            continue

        if _NOISE.search(line):
            pending_name = None
            continue

        # riga con percentuale: chiude il nome in sospeso (solo XI/panchina)
        m_pct = _PCT.match(line)
        if m_pct and pending_name and team and section in ("xi", "panca"):
            p = int(m_pct.group(1)) / 100.0
            key = (team, pending_name)
            records[key] = ProbRecord(
                name=pending_name, team=team, p_start=p,
                status=Status.OK, is_starter=(section == "xi"),
            )
            pending_name = None
            continue

        # riga bullet con un nome (eventualmente seguito da descrizione infortunio)
        name = line.lstrip("*").strip()
        # nelle sezioni stato il nome puo' avere una descrizione dopo: taglia
        # alla prima sequenza di 2+ spazi o dopo il primo pezzo prima di virgola lunga
        if section in ("squalificati", "infortunati", "dubbio"):
            if not name:
                continue
            if section == "dubbio":
                status_doubt_lines.append(name)
            else:  # squalificati o infortunati
                status_out_lines.append(name)
            continue

        # XI o panchina: memorizza il nome, la % arriva nelle righe successive
        if name and not name.startswith("#"):
            pending_name = name

    # applica lo stato: una riga stato riguarda il record il cui nome ne e'
    # prefisso (il nome piu' lungo vince, per evitare falsi positivi corti).
    def match(line: str, names: list[str]) -> str | None:
        cands = [n for n in names if line.startswith(n)]
        return max(cands, key=len) if cands else None

    all_names = [name for (_, name) in records]
    out_names = {match(l, all_names) for l in status_out_lines} - {None}
    doubt_names = {match(l, all_names) for l in status_doubt_lines} - {None}

    out: list[ProbRecord] = []
    for (team, name), rec in records.items():
        if name in out_names:
            rec.status = Status.OUT
        elif name in doubt_names:
            rec.status = Status.DOUBTFUL
        out.append(rec)
    return out


def fetch_html(url: str = "https://www.fantacalcio.it/probabili-formazioni-serie-a") -> str:
    """Scarica la pagina. Se 'requests' viene bloccato, usare il fallback
    Playwright (vedi README). Separato dal parsing di proposito."""
    import requests  # import locale: la dipendenza serve solo qui

    headers = {"User-Agent": "Mozilla/5.0 (compatible; fanta-bot/0.1)"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    # riduzione grezza HTML->testo per riusare lo stesso parser
    from html.parser import HTMLParser

    class _Text(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []

        def handle_data(self, d: str) -> None:
            self.parts.append(d)

    p = _Text()
    p.feed(r.text)
    return "\n".join(part.strip() for part in p.parts if part.strip())
