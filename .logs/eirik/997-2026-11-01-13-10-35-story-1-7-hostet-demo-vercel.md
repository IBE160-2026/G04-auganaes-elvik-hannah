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

## 2026-11-01 kl. 14:23 — Eirik

### Oppgave
Implementere Story 1.7 fra den godkjente spec-en, gjøre del B i Vercel, lage PR, sjekke preview og produksjon, og flette.

### Plan
- `bmad-build` steg 3–5 fra [`spec-1-7-hosted-demo-vercel-services-neon.md`](../../_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md). En subagent implementerte, og tre parallelle reviewere (Blind Hunter, Edge Case Hunter og Verification Gap) fulgte. Funnene ble vurdert mot koden og ført i spec-ens Review Triage Log.
- Del B i Vercel-dashbordet (Eirik), push og PR #8, sjekk av preview, `bmad-walkthrough` som review, deretter merge.

### Resultat
- Kode i fem commits: `65d80c1` (backend: URL-normalisering, `/api/health/db`, xact-lås, CORS fjernet), `91af51b` (Vite-proxy, Vitest delt i to prosjekter), `feeb162` (`vercel.json`, workflow for Neon-opprydding, Postgres 18, README), `9ab08dc` (arkitektur og epic-kontekst), `d09511d` (spec, review-funn og `korrigeringer.md`).
- Tester: 22 backend og 127 frontend, i tillegg til ruff, eslint og build. Alle 11 radene i I/O-matrisen er dekket. En bevisst feilende migrering ga exit 1 uten rester i databasen (utskriften står i PR-en).
- Review: 22 funn. 5 er rettet (`connect_timeout`, test av motor-innstillingene, `permissions: {}`, volumkommando som virker i PowerShell, og en README-merknad om bakoverkompatible migreringer). 6 er utsatt til `deferred-work.md`, og 11 er avvist.
- Del B er gjort: Root Directory tom og preset **Services** (navnet er bekreftet).
- Push krevde `workflow`-tilgang. Den ble lagt til med `gh auth refresh -s workflow`.
- Preview: `/`, `/service-worker.js`, `/api/health` og `/api/health/db` svarte 200. Eirik så `alembic_version` i Neon-grenen `preview/story/1-7-hosted-demo-vercel`, og det avklarte R8 (byggesteget kjører i `backend/`).
- KI-en fikk ikke lov til å flette uten review. Eirik gikk derfor gjennom PR-en med `bmad-walkthrough`, sjekket preview-en selv og godkjente. Reviewen er kommentert på PR #8, og PR-en er flettet (`ef1f455`).
- Produksjon (g04husly.vercel.app) svarer på de fire stiene, og `/api/health/db` gir `ok`. Workflowen slettet preview-grenen i Neon (steget fikk `success`), så R11 er avklart.
- Branchen `story/1-2-registration-login` har fått `main` inn med merge. 1.7 er satt til `done` (`421d293`), og KI-loggen er oppdatert (`5b49ea2`).

### Åpne punkter
- Bekrefte i Neon (SQL Editor, gren `main`) at `alembic_version` finnes. Produksjon svarer `ok`, men tabellen er ikke sjekket direkte.
- Story 1.2: sjekke at dype lenker (f.eks. `/login`) ikke gir 404 på Vercel (utsatt R10).
- Steffen bør teste lokal kjøring på Windows med Postgres 18 og Vite-proxyen.
