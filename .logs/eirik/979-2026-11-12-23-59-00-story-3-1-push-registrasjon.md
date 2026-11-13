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
