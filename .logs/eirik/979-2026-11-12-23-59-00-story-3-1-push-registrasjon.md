# Story 3.1: push-registrasjon

## 2026-11-12 kl. 23:59 — Eirik

### Oppgave
Merge PR #56 når CI var grønn, og start Story 3.1 (issue #55, push-registrering) med `bmad-build`. Trinn 2 begynner her, med FR-10 som Må.

### Plan
- Merge #56, `git checkout main && git pull`, ny branch `story/3-1-push-registrasjon`.
- Kompilere `epic-3-context.md` selv (ingen subagent før Eirik godkjente det) og skrive spec: [`spec-3-1-push-notification-permission-device-registration.md`](../../_bmad-output/implementation-artifacts/spec-3-1-push-notification-permission-device-registration.md).
- Spec-gjennomgang med Eirik ga fem rettelser: utlogging fjerner enhetens rad, stille registrering når tillatelsen allerede er gitt, ingen venting uten service worker (dev), tak på 10 per bruker, sporbarhet (sprint-status, PR lenker #55).
- Implementere direkte, kjøre tre reviewere (Blind Hunter, Edge Case Hunter, Verification Gap) etter Eiriks godkjenning, og rette patch-funn.

### Resultat
- PR #56 merget (CI grønn). Story 3.1 committet lokalt på `story/3-1-push-registrasjon` som `76a6639` (ikke pushet, ingen PR ennå).
- Backend: tabellen `push_subscriptions` (migrering `e5b7c9d1f3a2`, testet på midlertidig Postgres: upgrade, check, downgrade, upgrade), `domain/push.py`, `routes/push.py` (`GET /api/push/config`, `PUT` og `DELETE /api/push/subscriptions`), fast dev-VAPID-nøkkel i mock-modus, bare ASCII-https som endpoint.
- Frontend: `api/push.ts`, «Varsler» i Innstillinger, lukkbart notat på oppgaveoversikten når push er blokkert og noe forfaller, push- og `notificationclick`-handlere i `service-worker.ts`, lenkesjekk med `new URL`.
- Tester: backend 707, frontend 467, lint og bygg grønt. Kappløpstesten for `IntegrityError` feiler når grenen brytes.
- Dokumenter: FR-10 og kontodata i PRD (med Revision log-rad), note i `epics.md`, README og `.env.example`, `deferred-work.md` (fire punkter), `korrigeringer.md` (fire rader), Review Triage Log i spec.
- Rettet underveis: dobbel registrering etter ett trykk (testen fanget det), og datoen 13.11 skrevet to steder (rettet til 12.11).
- Sprint-status: 3-1 = `review`, epic-3 = `in-progress`. Spec-status `done`.

### Åpne punkter
- Push branchen, lag PR (lenk issue #55, beskriv test og hva som ble rettet i KI-forslaget), `bmad-walkthrough`, og merge på Eiriks ord. Etter merge: sprint-status 3-1 til `done` og statusoppdatering i CLAUDE.md.
- Eirik: teste i ekte nettleser med `npm run build && npm run preview` (service workeren registreres bare i produksjonsbygg): grant, deny, andre profil som andre enhet, og se to rader i `push_subscriptions`. Sjekk også Vercel Preview med Neon-migrering.
- Før Story 3.2: avgjøre om `domain/tasks.py` splittes og om «i dag» er norsk dag i stedet for UTC-dag (ligger allerede åpent fra Epic 2-retroen).
- Story 3.2 må sjekke at endepunktet ikke peker mot intern adresse, fokusere åpent vindu ved `notificationclick` og sette `tag`/`icon`, og håndtere ny abonnering når ekte VAPID-nøkler settes (alt i `deferred-work.md`).

## 2026-11-13 kl. 21:39 — Eirik

### Oppgave
Fullføre Story 3.1 (PR, test, walkthrough, merge), ta beslutningen om norsk dag og `domain/tasks.py` som stod åpen før Story 3.2, og gjøre klart for å bygge 3.2 i ny terminal.

### Plan
- Pushe branchen og lage PR #57, sjekke CI, kjøre testene lokalt, og starte database, backend og preview-bygg for Eiriks manuelle røyktest av push.
- Kjøre `bmad-walkthrough` på PR #57 og merge etter Eiriks godkjenning.
- Statuscommit etter merge, og en egen liten PR for beslutningen om dag og `domain/tasks.py` (retro-tiltak 3).
- Opprette issue og branch for Story 3.2 og gi Eirik en startprompt for ny terminal.

### Resultat
- PR #57 (Story 3.1) merget, merge-commit `7e56442`. Lokalt: backend 707 og frontend 467 tester grønne, `ruff`, `eslint` og bygg grønt. CI grønn på alle jobber. Eirik testet push manuelt i produksjonsbygg.
- Walkthrough: seks konsern og fem risikopunkter (utlogging best effort, upsert flytter rad mellom brukere, SSRF i 3.2, `DELETE` med body, VAPID-nøkkelbytte).
- PR #58 (status etter 3.1: sprint-status 3-1 = `done`, CLAUDE.md, KI-logg README) merget, merge-commit `b4fc7cd`.
- Beslutning (PR #59, merge-commit `1e2037c`, retro-tiltak 3 = `done`): UTC-døgnet beholdes, siden cron `0 6 * * *` UTC er samme kalenderdag i Norge, og 3.2 legger inn én `clock.utc_today()`. `domain/tasks.py` splittes ikke: forfallsjobben går i `domain/due_check.py`, fairness i `domain/fairness.py`, og `_is_open`/`_is_active` gjøres offentlige. Splitt når 3.3 må endre `_rows` eller filen når ca. 650 linjer. PRD og arkitektur er uendret. Beslutningen står i `sprint-status.yaml` og `epic-3-context.md`.
- Issue #60 (Story 3.2) og branch `story/3-2-due-check-jobb` laget fra `main`. Eirik bygger 3.2 i ny terminal med `bmad-build`.
- Rettet underveis: PR-teksten til #58 sa at `git status` var rent, men Stop-hooken eksporterte øktloggen på nytt. Første forsøk på å oppdatere filer med `sed -i` feilet på macOS, byttet til Python.

### Åpne punkter
- Story 3.2 (issue #60) skal bygges. Spec-en må ta med vertssjekk av push-adressen (SSRF), utlogging som best effort, `DELETE` med body på Vercel og VAPID-nøkkelbytte, i tillegg til `deferred-work.md`.
- `CRON_SECRET` må settes i Vercel (Preview først) av Eirik før cron kan testes hostet, og README og `.env.example` oppdateres i samme PR.
- Test av `DELETE` med body og push-registrering på Vercel Preview mot Neon er ikke gjort.
