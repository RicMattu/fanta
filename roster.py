"""La tua rosa (28 giocatori), letta dalla schermata di Leghe FC.

Ogni riga: (nome_come_su_fantacalcio.it, squadra, {ruoli ammessi}).

I RUOLI qui sono una prima assunzione mia, in chiaro, così puoi correggerli
a colpo d'occhio. Nel Mantra i ruoli veri sono piu' fini (Dc, Ds, E, W, T...);
lo script in cloud puo' sovrascriverli leggendo la colonna ufficiale dalle
Quotazioni di fantacalcio.it. Finche' non lo attiviamo, valgono questi.

Convenzione classica per i vincoli di modulo:
  P = portiere, D = difensore, C = centrocampista, A = attaccante.
Le ALI (Orsolini, Politano, Cancellieri, Vlasic, Colpani, Leao) hanno DOPPIO
ruolo {C, A}: l'ottimizzatore puo' usarle in mezzo o davanti, come nel Mantra.
Correggi tu se in lega un'ala non puo' fare l'attaccante.
"""

from .models import Role

# (nome, squadra, ruoli)
ROSTER: list[tuple[str, str, set[Role]]] = [
    # --- Portieri ---
    ("Mandas", "Lazio", {Role.P}),
    ("Maignan", "Milan", {Role.P}),
    ("Terracciano", "Milan", {Role.P}),
    # --- Difensori ---
    ("Couto", "Como", {Role.D}),
    ("Bellanova", "Atalanta", {Role.D}),        # esterno basso
    ("Zortea", "Bologna", {Role.D}),            # esterno basso
    ("Vasquez", "Genoa", {Role.D}),
    ("Gallo", "Lecce", {Role.D}),               # esterno basso
    ("Circati", "Parma", {Role.D}),
    ("Rrahmani", "Napoli", {Role.D}),
    ("Mina", "Cagliari", {Role.D}),
    ("Stones", "Inter", {Role.D}),
    # --- Centrocampisti ---
    ("Romano", "Cagliari", {Role.C}),
    ("Basic", "Venezia", {Role.C}),
    ("Winks", "Cagliari", {Role.C}),
    ("Mandragora", "Fiorentina", {Role.C}),
    ("Barella", "Inter", {Role.C}),
    ("Unai Gomez", "Udinese", {Role.C}),
    ("Rodriguez Je.", "Como", {Role.C}),
    # --- Ali / trequartisti: doppio ruolo C/A ---
    ("Vlasic", "Torino", {Role.C, Role.A}),
    ("Colpani", "Monza", {Role.C, Role.A}),
    ("Cancellieri", "Lazio", {Role.C, Role.A}),
    ("Orsolini", "Bologna", {Role.C, Role.A}),
    ("Politano", "Napoli", {Role.C, Role.A}),
    ("Leao", "Milan", {Role.C, Role.A}),
    # --- Attaccanti puri ---
    ("Vitinha O.", "Genoa", {Role.A}),
    ("Dovbyk", "Bologna", {Role.A}),
    ("Borrelli", "Cagliari", {Role.A}),
]
