# Formazione fantacalcio — app + job automatico

Due parti:
- **web/** — la pagina che apri sul telefono. Legge `web/dati.json` e mostra
  formazione, modulo, titolarità, voto e note. Nessun Python da lanciare.
- **build_dati.py + fanta/** — il job che gira su GitHub (i loro server),
  scarica le probabili da fantacalcio.it, ottimizza e riscrive `web/dati.json`.

## Cosa è già completo e cosa arriva dopo

Completo: titolarità e stato (infortuni/squalifiche) reali da fantacalcio.it,
ottimizzatore Mantra (modulo + XI, con doppio ruolo per le ali).
Da innestare (segnati come TODO in `build_dati.py`): il **voto atteso**
(fantamedia dalla pagina Quotazioni) e la **nota-notizie 24h**. Finché non ci
sono, l'ottimizzazione è sulla sola titolarità — cioè la "media di titolarità".

## Passo-passo per pubblicarla (una volta sola)

1. **Account**: crea un account su github.com se non ce l'hai (gratis).

2. **Nuovo repository**: in alto a destra, "+" → "New repository".
   Nome: `fanta` (o come vuoi). Mettilo **Public** (serve per Pages gratis).
   Crea.

3. **Carica i file**: nella pagina del repo vuoto, "uploading an existing file",
   trascina TUTTO il contenuto di questa cartella (la cartella `.github`, la
   cartella `fanta`, `web`, `build_dati.py`, `requirements.txt`). Commit.

4. **Attiva Pages**: Settings → Pages → "Build and deployment" → Source:
   "Deploy from a branch" → Branch: `main`, cartella: `/web` → Save.
   Dopo un minuto l'indirizzo appare in cima alla stessa pagina:
   `https://TUONOME.github.io/fanta/`.

5. **Sul telefono**: apri quell'indirizzo, poi "Aggiungi a schermata Home".
   Vedi già la formazione d'esempio (il `web/dati.json` incluso).

6. **Accendi l'automatismo**: Actions (tab in alto) → se chiede, abilita i
   workflow → scegli "aggiorna-formazione" → "Run workflow" per il primo giro.
   Da lì gira da solo agli orari nel file `.github/workflows/update.yml`
   (modificabili: sono in UTC).

## Se fantacalcio.it blocca il download diretto

Il job usa `requests`. Se prende un errore 403 (anti-bot), si passa a
caricare la pagina con Playwright e passare il testo allo stesso parser: dimmelo
e ti do la variante di `fetch_html`. Verifica anche i Termini di Servizio del
sito prima di automatizzare lo scraping ricorrente.

## Rosa e ruoli

La tua rosa è in `fanta/roster.py`, con i ruoli come assunzione documentata
(le ali hanno doppio ruolo C/A). Correggi lì se serve. In futuro i ruoli veri
Mantra possono essere letti dalla pagina Quotazioni.
