# Story 1.9: én regel for å opprette hjem

## 2026-11-10 kl. 18:25 — Eirik

### Oppgave
Fortsette arbeidet etter correct-course 09.11: bygge Story 1.9 (issue #30) med `bmad-build`, kjøre manuell test, pushe og lage PR, gjennomgå med `bmad-walkthrough` og merge.

### Plan
- `bmad-build` for Story 1.9: bygge Epic 1-konteksten på nytt, undersøke koden, skrive spec, avklare åpne spørsmål, kjøre adversarial spec-review, implementere med subagent og la tre reviewere se gjennom koden.
- Spec: [`spec-1-9-one-rule-for-creating-homes.md`](../../_bmad-output/implementation-artifacts/spec-1-9-one-rule-for-creating-homes.md).
- Manuell test mot en engangsdatabase (`husly_smoke`, backend på :8001, Vite på :5174), så Eiriks lokale `husly` og serverne hans ikke ble berørt.

### Resultat
- **Beslutninger (Eirik):**
  - Hytte eller flere husstandshjem holdes utenfor og er lagt i issue #34 som en mulig senere versjon. Grensen skal bare stå i én funksjon (`lived_in_home`).
  - 1A: `/` viser det nyeste hjemmet fram til 2.2.
  - 2A: tittel og ingress på «Opprett hjem» følger det som tilbys.
- **Spec-review:** 15 funn, og alle ble tatt inn. Det viktigste var at utkastet ville kopiert regelen inn i frontend-cachen.
- **Implementert:** `lived_in_home` og `_types_for` i `domain/homes`, `HomesOut.lived_in_home_id`, ny `routes/messages.py`, og 409 med samme melding som ved invitasjon. I tillegg tekst på «Opprett hjem», seed-sjekker, README-avsnittet «Prøv regelen for å opprette hjem» og en kildetest for at grensen bare står ett sted.
- **Kodegjennomgang:** 14 funn fra tre reviewere: 6 rettet, 1 utsatt (seed for Jonas, i `deferred-work.md`) og 7 avvist. Rettelsene er ført inn i `korrigeringer.md`.
- **Tester:** 474 backend-tester og 288 frontend-tester passerer, og CI er grønn på Linux og Windows.
- **Manuell test:** API-et og Chrome for Kari, Jonas og Anders er testet, og `fr3_violations` var tom. Eirik testet Vercel-previewen, og alt fungerte.
- **Walkthrough:** gjort. Eirik foreslo at Husly-logoen skal lenke til `/`, og det er lagt inn som AC i Story 2.2.
- **Commits:**
  - `f1e7d72` (spec), `33b6198` (implementering), merget i PR #35 (`8dde3b2`). Issue #30 er lukket.
  - Statusoppdatering og logo-AC er på branch `chore/status-etter-story-1-9` → PR #36. Der er 1-9 og epic-1 satt til done, CLAUDE.md er oppdatert, og KI-logg-raden er lagt inn.
- Punktet «Story 1.9 med `bmad-build`» i `issues.md` er lukket.

### Åpne punkter
- Story 2.2 må ta med det nye AC-et om at Husly-logoen lenker til `/` (`epics.md`, PR #36).
- Hytte eller flere husstandshjem per bruker (issue #34) er en mulig senere versjon og skal planlegges med correct-course.
- Seed: `_seed_household` bør bruke `join_blocker` for Jonas (`deferred-work.md`).
- Sjekke i Neon at preview-branchen for PR #35 er slettet.
