# Story 2.6: legge til og fjerne oppgaver

## 2026-11-12 kl. 19:05 — Eirik

### Oppgave
Fortsette med Story 2.6 (issue #31, FR-24) etter correct-course for faglærers PRD-tilbakemelding, med `bmad-build`. PR #44 (2.4 og 2.5) var ikke merget, så storyen ble bygget stablet på 2.4-branchen.

### Plan
- Epic 2-konteksten ble oppdatert (den var gammel etter 2.3 og 2.4), og 2.4-spec-en ble lest for kontinuitet.
- Eirik svarte på fire spørsmål: én Add Task-side med radiovalg, knapp i oversiktens header, meldinger «La til «X»» og «Fjernet «X»», og 409 før oppsett er kjørt.
- Spec: [`spec-2-6-add-and-remove-tasks.md`](../../_bmad-output/implementation-artifacts/spec-2-6-add-and-remove-tasks.md). Uavhengig spec-review (15 funn, alle tatt inn), implementasjon direkte uten dispatch-subagent, tre reviewere på koden (Blind Hunter, Edge Case Hunter, Verification Gap), og røyktest i Chrome.

### Resultat
- Branch `story/2-6-legg-til-og-fjern-oppgaver` fra `story/2-4-self-checkoff`, **PR #46** mot 2.4-branchen (flyttes til `main` når #44 er merget). Commits: `60c287a` (spec, baseline), `dc20d13` (backend), frontend-commit, `de0a78d` (review-rettelser), `7bd121e` (ferdig til review), `e8d5f1b` (KI-logg).
- Backend: `add_task`/`archive_task`, `POST`/`DELETE /api/homes/{home_id}/tasks`, migrasjon `d7a3b5c9e2f1` med delvise unike indekser for aktive oppgaver, `photo_evidence_eligible`. Frontend: siden `/hjem/<id>/legg-til-oppgave`, header-knapp, tomtilstand, «Fjern oppgaven».
- Testet: 630 backend- og 423 frontend-tester, ruff, eslint og bygg; migrasjon opp/ned/opp og `alembic check` ren, prober og downgrade med data på Postgres 18 mot engangsdatabaser (alle slettet, `husly` urørt); CI-prober for indeksene; Chrome-røyktest.
- Reviewfunn er i spec-ens Review Triage Log og `docs/ki-logg/korrigeringer.md`. Ett funn utsatt: Tenant-teksten når alle oppgaver er arkivert (`deferred-work.md`).
- Svaret på Bårds refleksjonsspørsmål 2 er skrevet (`docs/ki-logg/refleksjon-prd-tilbakemelding-2026-11-12.md`, pushet på correct-course-branchen, PR #45). Linje om økten er lagt i `docs/ki-logg/README.md` på denne branchen.

### Åpne punkter
- Eirik: teste Vercel-previewen for PR #44 og PR #46 (migreringene `c4e1d2a7b9f3` og `d7a3b5c9e2f1` mot Neon-previewen), `bmad-walkthrough`, og merge #44 først, så #46.
- Statuscommit på main etter merge: 2.6 til `done`, og CLAUDE.md «Status».
- Rebase kan trengs mellom PR #44, #45 og #46 (alle endrer `epics.md`, `korrigeringer.md` eller KI-logg-filer).
- Tenant-tekst når alle oppgaver er arkivert er en UX-beslutning (`deferred-work.md`).

## 2026-11-12 kl. 20:15 — Eirik

### Oppgave
Merge PR-ene etter at Eirik hadde testet previewene, lage reviewer-sjekken for PRD, og ta statuscommiten. Eirik ba om en forklaring av preview-testen (ikke et dokument), så PR #48 med veiledningen ble lukket uten merge.

### Plan
- Merge i rekkefølgen #44, #46 (flyttet til `main`), #47 og #45. #45 hadde konflikter og fikk `main` slått inn.
- Statuscommit på en egen branch og PR.

### Resultat
- **Merget:** #44 (Story 2.4 og 2.5), #46 (Story 2.6), #47 (reviewerne sjekker PRD: ny «Required check» i `_bmad/custom/review-conventions.md`, de tre review-lagene i `bmad-build.toml` og en regel i CLAUDE.md), #45 (correct-course for faglærers PRD-tilbakemelding). **Lukket uten merge:** #48 (Vercel-veiledning); branchen er slettet.
- #45: konflikter i `issues.md`, `korrigeringer.md` og den eksporterte øktfilen ble løst ved å beholde begge sider (commit `2d20bf0`). `epics.md` og arkitekturen slo seg sammen uten konflikt.
- Eirik fikk «Noe gikk galt» ved registrering. Årsaken var en gammel preview (`story/1-9-create-rule`) hvis Neon-gren var slettet etter merge; `/api/health/db` svarte 503. Funnet i Vercel-loggene. #44 og #46 virket, og Eirik bekreftet at alt fungerte.
- Statuscommit `4312608` på `chore/status-etter-story-2-6`: 2.4, 2.5, 2.6 og epic-2 til `done`, og CLAUDE.md «Status».
- Ikke testet: den nye PRD-sjekken er ikke kjørt i en review ennå.

### Åpne punkter
- Merge statuscommit-PR-en.
- Neste story er 5.1 (KI «?»-svar); første review med PRD-sjekken. Må bygge `ai_usage`-migrasjon, 10 s timeout og 20 kall per dag (FR-14).
- UX-beslutning om tekst til leietaker når alle oppgaver er arkivert (`deferred-work.md`).
