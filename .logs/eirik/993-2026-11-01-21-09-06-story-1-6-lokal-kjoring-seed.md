# Story 1.6: lokal kjøring med seed-data og mock-modus

## 2026-11-01 kl. 21:09 — Eirik

### Oppgave
En kort økt der vi fortsatte fra forrige gang. Story 1.6 skulle bygges, slik at sensor kan kjøre appen lokalt med én seed-kommando og eksempelbrukere, uten gruppens kontoer eller nøkler (FR-22, AD-15).

### Plan
- Lage issue #12, deretter `bmad-build` fra planleggingen. Spec: [`spec-1-6-run-locally-docker-seed-mock.md`](../../_bmad-output/implementation-artifacts/spec-1-6-run-locally-docker-seed-mock.md).
- Gruppas beslutninger, tatt med tanke på sensorveiledningen:
  - ingen mock-indikator i UI ennå, avviket noteres i `epics.md`
  - seed kjører bare mot en lokal database
  - eksempelbrukerne er Mari Nordmann og Jonas Berg, med passordet `husly-demo`
- Spec-review, deretter implementering ved en subagent, deretter kodegjennomgang med tre reviewere, så walkthrough, PR og CI.

### Resultat
- **Kode** (`a1df9c5`):
  - `backend/app/seed/`: `uv run python -m app.seed` kjører migreringene og lager eksempelbrukerne gjennom `accounts.register`. Kommandoen kan kjøres flere ganger, og `STEPS` kan utvides av 1.3 og 2.1. Seed nekter å kjøre (exit 2) på Vercel og mot en database som ikke er lokal, og gir exit 1 med hint og den egentlige feilen når databasen er nede.
  - Tester: en nettverkssperre i `conftest.py`, `test_env_example.py` (sjekker begge veier og at `.env` er gitignored), `test_network_guard.py` og `test_seed.py`.
  - I tillegg ble CI, README og `.env.example` oppdatert.
- **Plan og spec** (`b1863d5`): spec-en med review-triage, et notat i `epics.md` om at mock-indikatoren kommer med 5.1, og utfall på e-post-punktet i `deferred-work.md`. Sprint-status for 1-6 er satt til `review`.
- **Review:** Spec-reviewen ga 15 funn, og alle ble tatt inn. Kodegjennomgangen ga 20 funn: 8 rettet, 8 avvist og 4 som ikke stemte. Fire rettelser er notert i `docs/ki-logg/korrigeringer.md`.
- **Verifisert:**
  - 129 tester grønne, og ruff er ren.
  - CI på PR #13 er grønn i alle sju sjekkene, også på Windows. Seed lagde brukerne ved første kjøring, ga «finnes allerede» ved andre og hint ved lukket port.
  - Eirik logget inn som Mari og Jonas i Chrome og Safari, og testet seed med stoppet database.
- **KI-logg:** `5492177`, og tidligere økter i `0c9ff05`.
- PR #13: <https://github.com/IBE160-2026/G04-auganaes-elvik-hannah/pull/13>. Spørsmålet om MCP-servere i økta: Claude Docs og Vercel-MCP er koblet til, men trengs ikke.
- Løste punkter i `issues.md`: seed lager brukere via `accounts.register`.

### Åpne punkter
- Steffen: følge README-en fra start i Git Bash på Windows på branchen for PR #13 (seed, `pytest` og innlogging som Mari), og legge resultatet som kommentar på PR-en. Dekker også det åpne punktet fra 1.7.
- Etter Steffens test: eventuelt resten av `bmad-walkthrough` (detaljer og testing), merge PR #13, sette 1-6 til `done` i sprint-status og oppdatere status i CLAUDE.md. Neste story er 1.3, som utvider `STEPS` med et eksempel-Home.

## 2026-11-07 kl. 23:19 — Eirik

### Oppgave
Steffen er fortsatt på ferie. Vi ville komme videre uten å vente på hans Windows-test før PR #13 ble merget.

### Plan
- Merge PR #13 før den manuelle testen på Windows, med begrunnelsen i PR-en, og flytte testen til en egen issue for Steffen.
- Fortsette med Story 1.3 fra `main` (se [story-1-3-opprette-hjem](992-2026-11-07-23-19-16-story-1-3-opprette-hjem.md)).

### Resultat
- KI-logg for økten om 1.6 committet (`9884d2b`).
- Issue #14 opprettet og tildelt Steffen (`Steelvik`): følg README i Git Bash på `main`.
- PR #13 har en kommentar om risikoen. CI på `windows-latest` dekker pytest, ruff, Vitest og bygg, men ikke Docker og Git Bash fra en helt ny klone. Avkrysningen er flyttet til #14.
- PR #13 merget (`c2bcfc7`). 1-6 satt til `done`, og CLAUDE.md pekte på 1.3 (`38f5e49`, første commit på `story/1-3-create-home`).

### Åpne punkter
- Steffen: issue #14, README i Git Bash på Windows på `main`.
