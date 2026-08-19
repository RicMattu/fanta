"""Ottimizzatore con ruoli multipli.

Nel Mantra un giocatore puo' occupare slot di ruoli diversi. Diventa un
ASSEGNAMENTO: variabile binaria x[giocatore, ruolo] = 1 se schierato IN quel
ruolo, definita solo per i ruoli ammessi del giocatore.

    max  sum_{i,r}  E[punti]_i * x[i,r]
    s.t. sum_r x[i,r] <= 1              (ogni giocatore al piu' una volta)
         sum_i x[i,r] = req[r]          (slot esatti per ruolo, dal modulo)

Si risolve un ILP per modulo e si tiene il migliore.
"""

from __future__ import annotations

from dataclasses import dataclass

import pulp

from .models import MANTRA_FORMATIONS, Player, Role, role_requirements


@dataclass
class Lineup:
    formation: str
    starters: list[tuple[Player, Role]]  # giocatore e ruolo in cui e' schierato
    score: float

    def by_role(self) -> dict[Role, list[Player]]:
        out: dict[Role, list[Player]] = {r: [] for r in Role}
        for p, r in self.starters:
            out[r].append(p)
        return out


def best_xi(players: list[Player], formation: str) -> Lineup | None:
    req = role_requirements(formation)
    usable = [p for p in players if p.adjusted_p() > 0]

    # fattibilita': per ogni ruolo servono abbastanza giocatori ammessi
    for role, n in req.items():
        if sum(1 for p in usable if role in p.roles) < n:
            return None

    prob = pulp.LpProblem("mantra", pulp.LpMaximize)
    x: dict[tuple[int, Role], pulp.LpVariable] = {}
    for i, p in enumerate(usable):
        for r in p.roles:
            x[(i, r)] = pulp.LpVariable(f"x_{i}_{r.value}", cat="Binary")

    prob += pulp.lpSum(usable[i].expected_points() * v for (i, _), v in x.items())

    for i, p in enumerate(usable):                     # al piu' una volta
        vars_i = [x[(i, r)] for r in p.roles]
        if vars_i:
            prob += pulp.lpSum(vars_i) <= 1

    for role, n in req.items():                        # slot esatti per ruolo
        prob += pulp.lpSum(v for (i, r), v in x.items() if r is role) == n

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[prob.status] != "Optimal":
        return None

    starters = [(usable[i], r) for (i, r), v in x.items() if v.value() == 1]
    score = sum(p.expected_points() for p, _ in starters)
    return Lineup(formation=formation, starters=starters, score=score)


def best_lineup(players: list[Player], formations: list[str] | None = None) -> Lineup | None:
    formations = formations or list(MANTRA_FORMATIONS.keys())
    best: Lineup | None = None
    for f in formations:
        cand = best_xi(players, f)
        if cand and (best is None or cand.score > best.score):
            best = cand
    return best
