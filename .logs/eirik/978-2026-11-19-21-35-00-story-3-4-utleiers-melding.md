# Story 3.4: utleiers melding til leietakerne

## 2026-11-19 kl. 21:35 — Eirik

### Oppgave
Eirik ga Claude mandat i en time til å følge CLAUDE.md og BMAD-oppsettet og ta egne valg, etter først å ha spurt om Claude hadde kontroll fra sist. Rollback-punktet skulle hete «Før claude fikk mandat».

### Plan
- Punkt 1–3 fra forrige økt: hent status, sett 3.2 til `done`, oppdater Status i `CLAUDE.md`. Egen commit «Før claude fikk mandat» som rollback.
- Bygg neste story i rekkefølgen fra planen med `bmad-build`: Story 3.4 (FR-12), siden 3.3 er «hvis tid». Spec: [`spec-3-4-landlord-ad-hoc-broadcast-message.md`](../../_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md).
- Tre reviewere, retting av funn, PR uten merge.

### Resultat
- Status: PR #62 (`docs/status-etter-story-3-2`) setter 3.2 til `done` og retter Status i `CLAUDE.md`. Claude hadde først skrevet 3.3 som neste story, men epics.md legger FR-11 under «hvis tid», så 3.4 er riktig.
- Rollback: commit `0e7018e` «Før claude fikk mandat», tag `for-claude-fikk-mandat`.
- Story 3.4: PR #64 (issue #63, branch `story/3-4-utleier-melding`). `POST /api/homes/{id}/broadcast` (bare utleier, 1–300 tegn, 409 uten leietakere), `push.deliver` delt med forfallsjobben, `HomeOut.can_broadcast`, siden `/hjem/<id>/utleier` som skall for utleieradmin. PRD FR-12, epics, AD-14 og README er oppdatert, med én rad i Revision log.
- Review: Blind Hunter, Edge Case Hunter og Verification Gap. Rettet blant annet «Prøv igjen» som ikke bekreftet, tekst som ble slettet når ingen ble nådd, og en 403-test som kunne bestå for tidlig. Alt står i spec-ens Review Triage Log og `docs/ki-logg/korrigeringer.md`.
- Testing: backend 788 grønne lokalt. Frontend kunne ikke kjøres lokalt (vitest får ikke startet arbeideren, `node_modules` leses for sakte). CI fant én feil (klienten sendte utrimmet tekst), rettet i `2563710`, og alle CI-jobber er grønne. PR #64 er merket klar til review.
- Ikke merget noe. Ikke pushet annet enn de to branchene.

### Åpne punkter
- Eirik: les valgene Claude tok i spec 3.4 under «Decisions» (300 tegn, ingen daglig grense, tekst «kunne ikke nås med varsel», skallet bygges her), og godkjenn eller endre.
- Eirik: I/O-matrisen i spec 3.4 sier «3 pushes», riktig er 2. Den frosne blokken er ikke rørt.
- Eirik: merge PR #62 og #64 etter review. `sprint-status.yaml` kan få triviell konflikt på `last_updated`. Etter merge: 3.4 til `done` og Status i `CLAUDE.md`.
- Vitest starter ikke lokalt på denne maskinen i denne sesjonen (arbeider-timeout 60 s, filleseing i `node_modules` svært treg). Undersøk før neste story hvis det vedvarer.
- Neste i planen: Story 3.5 (FR-13) og Epic 4; 3.3 er «hvis tid». Utsatte punkter fra 3.4 står i `deferred-work.md`.
