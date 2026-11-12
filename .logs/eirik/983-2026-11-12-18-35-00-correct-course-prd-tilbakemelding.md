# Correct-course: faglærers PRD-tilbakemelding

## 2026-11-12 kl. 18:35 — Eirik

### Oppgave
Følge opp Bård Pettersens formative tilbakemelding på PRD-en (f76b547) med `bmad-correct-course`, inkrementelt og på coaching path. Eirik godkjente alt alene fordi Hannah og Steffen ikke var tilgjengelige.

### Plan
- Les PRD, `epics.md`, arkitekturspinen og `technology.md` (som viste seg å beskrive et annet prosjekt og bare ga to ideer: mock uten nøkler, og rate limiting på KI).
- Seks forslag ble godkjent ett og ett: kuttlinje, testbare krav, KI-feil/kost/data, rene krav og Revision log, FR-2/FR-3 og SM-ene, mekaniske funn og kontopersonvern.
- Samlet i [`sprint-change-proposal-2026-11-12.md`](../../_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-12.md), deretter innført i PRD, epics og arkitektur.

### Resultat
- Ny branch `docs/correct-course-2026-11-12` fra `origin/main` (ikke fra Story 2.4-branchen). Commits `20c2657` (planleggingsdokumenter og `korrigeringer.md`) og `f9575a1` (KI-logg for økten). Pushet, **PR #45** opprettet.
- Beslutninger: Trinn 2 Must = FR-10, 12, 13, 18/19; hvis tid kuttes FR-20, FR-16, FR-11, FR-15 i den rekkefølgen. FR-11 = ingen av de 3 siste, minst to medlemmer og tre fullførte, bare mens oppgaven er åpen, maks én per forekomst. KI: 10 s timeout, 20 kall per bruker per dag (`ai_usage`), minimalt innhold i kallet, UI-linje om ekstern tjeneste. Sletting av konto er ikke bygget («vil vi prøve å få til», ca. én dag).
- Funn mot koden: appen har ingen «unit type», så FR-16 er skrevet om til Homets navn og aktive Must-oppgaver. Tre rader lagt i `docs/ki-logg/korrigeringer.md`.
- Ingen kode endret, ingen tester kjørt. Kontrollert med grep at gamle merker og kodeord er borte fra kravteksten.

### Åpne punkter
- PR #45 må leses av Hannah og Steffen, særlig kuttlinjen. De kan protestere der.
- PR #44 (Story 2.4/2.5) er fortsatt åpen og endrer også `epics.md` og arkitekturen. Rebase hvis PR #45 eller #44 gir konflikt.
- Story 3.3 (FR-11) og Story 5.1 (`ai_usage`-migrasjon, timeout, dagsgrense) må bygges etter de nye kriteriene. Story 5.1 trenger en Alembic-migrasjon.
- Svar på Bårds refleksjonsspørsmål 2 (hva vi tok fra koden tilbake til kravene) skal inn i `docs/ki-logg/`.
- Linje om økten mangler i sammendragstabellen i `docs/ki-logg/README.md`.
