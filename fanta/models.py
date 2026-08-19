"""Modello dati.

Rispetto alla versione base, un giocatore ha un INSIEME di ruoli ammessi
(per il Mantra: un'ala puo' valere centrocampo o attacco). L'obiettivo per
giocatore resta E[punti] = p * v, indipendente dal ruolo in cui lo schieri.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    P = "P"
    D = "D"
    C = "C"
    A = "A"


class Status(str, Enum):
    OK = "ok"
    DOUBTFUL = "dubbio"
    OUT = "out"


@dataclass
class Player:
    name: str
    team: str
    roles: set[Role]
    p_start: float = 0.0       # titolarita' (gia' corretta per ballottaggi)
    exp_vote: float = 6.0      # E[voto | gioca]; default 6 = ottimizzazione su sola titolarita'
    status: Status = Status.OK
    doubtful_factor: float = 0.5
    news: str = ""             # nota dalle ultime notizie (riempita dal job)

    def adjusted_p(self) -> float:
        if self.status is Status.OUT:
            return 0.0
        if self.status is Status.DOUBTFUL:
            return self.p_start * self.doubtful_factor
        return self.p_start

    def expected_points(self) -> float:
        return self.adjusted_p() * self.exp_vote


# Moduli Mantra ammessi -> conteggi (D, C, A). Il portiere e' sempre 1.
# ASSUNZIONE DOCUMENTATA: il trequartista e' contato tra i centrocampisti (C).
# In un Mantra rigoroso alcuni slot sono ruoli esatti (T, W, E...): questa e'
# l'approssimazione a conteggi, sufficiente per scegliere l'XI sulla titolarita'.
# Se in lega un modulo va inteso diversamente, cambia qui i numeri.
MANTRA_FORMATIONS: dict[str, tuple[int, int, int]] = {
    "3-4-1-2": (3, 5, 2),
    "3-4-2-1": (3, 6, 1),
    "3-4-3":   (3, 4, 3),
    "3-5-1-1": (3, 6, 1),
    "3-5-2":   (3, 5, 2),
    "4-1-4-1": (4, 5, 1),
    "4-2-3-1": (4, 5, 1),
    "4-3-1-2": (4, 4, 2),
    "4-3-3":   (4, 3, 3),
    "4-4-1-1": (4, 5, 1),
    "4-4-2":   (4, 4, 2),
}


def role_requirements(formation: str) -> dict[Role, int]:
    d, c, a = MANTRA_FORMATIONS[formation]
    return {Role.P: 1, Role.D: d, Role.C: c, Role.A: a}
