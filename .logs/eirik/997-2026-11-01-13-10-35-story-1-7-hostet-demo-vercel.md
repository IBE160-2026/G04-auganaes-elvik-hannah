# Story 1.7: Hostet demo på Vercel

## 2026-11-01 kl. 13:10 — Eirik

### Oppgave
Flette correct-course-PR-en (#7) og starte Story 1.7 (issue #6): frontend og FastAPI på Vercel på samme domene, med Neon. Denne økten dekket planleggingen fram til godkjent spec. Implementeringen tas i en ny `bmad-build`-økt.

### Plan
- `bmad-build` med coaching path og reviewer gates. Epic 1-konteksten ble laget på nytt av en subagent, og en annen subagent undersøkte Vercel Services, Python og Neon.
- Spec: [`spec-1-7-hosted-demo-vercel-services-neon.md`](../../_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md) (`ready-for-dev`).

### Resultat
- PR #7 er flettet (`50fcdcd`). Branchen `story/1-7-hosted-demo-vercel` er laget fra main.
- Epic 1-konteksten er laget på nytt (`70b15a7`).
- Teambeslutninger: Neon og Vercel-funksjonene i EU (Frankfurt, `aws-eu-central-1` og `fra1`). Hele spec-en beholdes selv om den er over anbefalt lengde.
- Spec-review: 12 funn, 2 høye (advisory lock før Alembics transaksjon og sesjonslås gjennom PgBouncer). 11 er rettet, og 1 er beholdt med begrunnelse. Spec godkjent (`6e5726f`), og KI-loggen er oppdatert (`2163fc7`).
- Dashbord-steg i del A er gjort: Neon `husly-db` i Frankfurt, koblet til `g04husly` med preview-branching (Production og Preview har `DATABASE_URL` og `DATABASE_URL_UNPOOLED`). Funksjonsregionen er `fra1`. I GitHub ligger variabelen `NEON_PROJECT_ID` (`hidden-hat-61977415`, satt med `gh`) og secreten `NEON_API_KEY` (lagt inn av Eirik). Neon ga Postgres 18.6 uten mulighet til å velge versjon, så spec-en har fått en oppgave om å oppgradere Docker lokalt til 18 (`43f7f94`).
- Eirik valgte «Godkjenn og stopp», fordi økten var lang og dashbord-stegene må gjøres før previewen kan testes.

### Åpne punkter
- Del B rett før koden pushes: Root Directory tom (repo-roten) og Framework Preset **Services**. Ingen andre flettinger til main før 1.7 er inne.
- Start en ny `bmad-build`-økt med spec-filen for å implementere Story 1.7.
