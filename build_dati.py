"""Job che gira in cloud (GitHub Actions) e produce web/dati.json.

Passi:
  1. carica la tua rosa (roster.py);
  2. scarica le probabili da fantacalcio.it e prende la titolarita' (p) e lo
     stato (infortuni/squalifiche) di ogni tuo giocatore;
  3. [DA COMPLETARE] fantamedia (v) e nota-notizie 24h per ogni giocatore;
  4. ottimizza formazione + modulo;
  5. scrive web/dati.json, che l'app sul telefono legge.

STATO ATTUALE (v1, onesto):
  - titolarita' e stato: REALI, dallo scraper testato.
  - voto atteso v: default 6.0 -> l'ottimizzazione e' sulla sola TITOLARITA'.
  - notizie 24h: placeholder vuoto.
  Questi due (v e notizie) sono i prossimi innesti; il resto e' completo.

Nota: se il download diretto (requests) viene bloccato, sostituire fetch_probabili
con un caricamento via Playwright (vedi README). Il parsing non cambia.
"""

from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

from fanta.models import Player, Status
from fanta.optimizer import best_lineup
from fanta.roster import ROSTER
from fanta.scraper_fantacalcio import ProbRecord, fetch_html, parse

OUT = Path(__file__).resolve().parent / "web" / "dati.json"


def _norm(s: str) -> str:
    """Normalizza un nome per il confronto (accenti, maiuscole, spazi)."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().strip()


def match_titolarita(records: list[ProbRecord]) -> list[Player]:
    """Costruisce i Player della TUA rosa agganciando la titolarita' scrapata."""
    # indicizza i record per (squadra_norm, nome_norm) e per solo nome_norm
    by_team_name = {(_norm(r.team), _norm(r.name)): r for r in records}
    by_name = {_norm(r.name): r for r in records}

    players: list[Player] = []
    for name, team, roles in ROSTER:
        rec = by_team_name.get((_norm(team), _norm(name))) or by_name.get(_norm(name))
        if rec is None:
            # non trovato tra le probabili (es. non convocato): titolarita' 0
            players.append(Player(name=name, team=team, roles=roles,
                                   p_start=0.0, status=Status.OK))
            continue
        players.append(Player(
            name=name, team=team, roles=roles,
            p_start=rec.p_start, status=rec.status,
            exp_vote=6.0,   # TODO: fantamedia reale
            news="",        # TODO: notizie 24h
        ))
    return players


def build() -> dict:
    html_or_text = fetch_html()          # scarica la pagina probabili
    records = parse(html_or_text)        # estrae titolarita' + stato
    players = match_titolarita(records)

    lineup = best_lineup(players)
    if lineup is None:
        raise SystemExit("Nessuna formazione fattibile: controlla la rosa/scraping.")

    data = {
        "modulo": lineup.formation,
        "punteggio_atteso": round(lineup.score, 1),
        "titolari": [
            {"nome": p.name, "squadra": p.team, "ruolo": r.value,
             "titolarita": round(p.adjusted_p() * 100),
             "voto": round(p.exp_vote, 1),
             "stato": p.status.value, "news": p.news}
            for p, r in lineup.starters
        ],
        "aggiornato": __import__("datetime").datetime.now().strftime("%d/%m %H:%M"),
    }
    return data


def main() -> None:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scritto {OUT}  modulo={data['modulo']}  score={data['punteggio_atteso']}")


if __name__ == "__main__":
    main()
