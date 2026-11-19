# Story 3.5: utleiers varslingsfrekvens

## 2026-11-19 kl. 22:30 — Eirik

### Oppgave
Eirik ba Claude starte Story 3.5 (FR-13) etter at 3.4 var oppe som PR. Samme vilkår som før: følge CLAUDE.md og BMAD, ta egne valg, ikke merge.

### Plan
- `bmad-build` for 3.5 med spec: [`spec-3-5-landlord-controlled-notification-cadence.md`](../../_bmad-output/implementation-artifacts/spec-3-5-landlord-controlled-notification-cadence.md).
- Branch `story/3-5-varslingsfrekvens` oppå `story/3-4-utleier-melding`, siden 3.5 bruker utleierskallet fra 3.4 som ikke er merget.
- Tre reviewere, retting, CI, PR uten merge.

### Resultat
- PR #66 (issue #65), base `story/3-4-utleier-melding`, klar til review.
- `homes.notification_cadence_days` (1, 2 eller 7, standard 1) med migrering `c4e8a2f6b1d7`. Forfallsjobben varsler en leietaker om en åpen Må-oppgave når dagene siden frist går opp i frekvensen. `PUT /api/homes/{id}/notification-cadence` bare for utleier. Valget ligger på «Administrer hjemmet».
- Valg Claude tok (står i spec «Decisions»): 1/2/7 dager, bare leietakere og Må-oppgaver, fristdagen varsler alltid.
- Review: tre reviewere. Viktigst: CHECK-begrensningen var ikke bevist i det migrerte skjemaet (nå i CI-listen), valgene sto på fem steder, ingen test for hoppet dag. PRD FR-10/FR-13, epics, AD-8 og README rettet. Korrigeringer ført.
- Testing: backend 824 grønne lokalt. Frontend og migrering kjørte bare i CI, og alle jobber er grønne. Vitest starter fortsatt ikke lokalt, og Docker kjørte ikke.
- Ingenting merget.

### Åpne punkter
- Eirik: les og godkjenn Claudes valg i spec 3.5, og review PR #66.
- Eirik: merge i rekkefølge #62, #64, #66. Etter merge av #64 må basen på #66 byttes til `main`. Deretter 3.4 og 3.5 til `done` i `sprint-status.yaml` og Status i `CLAUDE.md` (3.5 står nå som `in-progress`).
- Neste i planen: Epic 4 (FR-18/19). 3.3 (FR-11) er «hvis tid».
