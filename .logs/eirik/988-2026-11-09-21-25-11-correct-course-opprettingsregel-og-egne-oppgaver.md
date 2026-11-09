# Correct-course: opprettingsregel og egne oppgaver

## 2026-11-09 kl. 21:25 — Eirik

### Oppgave
Kjøre `bmad-correct-course` for issue #30 (en utleier kan ikke opprette sitt eget husstandshjem) og #31 (brukere skal kunne legge til og fjerne oppgaver selv etter oppsettet).

### Plan
- Lese PRD, epics, arkitektur, UX, forrige endringsforslag og koden som berøres (`allowed_types`, `join_blocker`, `fr3_violations`, `HomePage.tsx`).
- Inkrementell modus: gå gjennom sjekklisten, stille spørsmål om beslutningene og legge fram åtte forslag ett om gangen.
- Gjøre endringene på branch `change/create-rule-and-custom-tasks` med én commit per dokument og åpne en PR.
- Forslaget: [`sprint-change-proposal-2026-11-09.md`](../../_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-09.md).

### Resultat
- Eirik tok åtte beslutninger:
  1. Én felles regel for å opprette hjem, som også lukker retrofunn R1. Den blir Story 1.9 og bygges før 2.2.
  2. Bytte mellom hjem løses i Story 2.2.
  3. Å fjerne en oppgave arkiverer den, og det finnes ingen gjenoppretting.
  4. Egne oppgaver må ha unikt navn og kan aldri kreve bildebevis.
  5. Legge til og fjerne oppgaver blir FR-24 og Story 2.6 i Trinn 1, bygget etter 2.5.
  6. Et hjem der alle oppgavene er arkivert, åpner ikke oppsettet igjen.
- Funn som ikke sto i issue-ene:
  - `fr3_violations` berøres ikke.
  - `/` viser bare det nyeste hjemmet.
  - Fjerning må være arkivering fordi historikken skal beholdes (AD-16).
  - 1.8 og FR-23 manglet flere steder etter forrige correct-course.
- Commits på branchen: `c658ee7` (forslaget), `00225e9` (PRD), `5b0e64a` (arkitektur), `6abb5db` (UX), `674cb86` (epics), `13211ae` (sprint-status), `093588e` (spor), `fdf610c` (memlogger) og en commit for status og KI-logg.
- `detect-epic` viser `1-9` og `2-6` som ventende. Branchen er pushet, og PR #33 er åpnet. Issue #30 og #31 har fått kommentarer.

### Åpne punkter
- Merge PR #33 (correct-course) når Eirik sier fra.
- Story 1.9 (én regel for å opprette hjem) med `bmad-build`, issue #30, branch `story/1-9-create-rule`, før Story 2.2.
- Story 2.2 må ta med den nye AC-en om bytte mellom hjem («Dine hjem», `/hjem/<id>`).
- Story 2.6 (legge til og fjerne oppgaver, issue #31) etter Story 2.5.
