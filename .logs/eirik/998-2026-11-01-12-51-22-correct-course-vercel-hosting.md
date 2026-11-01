# Correct-course: Vercel som eneste hosting

## 2026-11-01 kl. 12:51 — Eirik

### Oppgave
Faglærer gjorde Vercel til eneste hosting i emnet. Planen måtte justeres med `bmad-correct-course` før Story 1.2 bygges, fordi innloggingen var designet for frontend og backend på to ulike domener.

### Plan
- Coaching path og inkrementell modus: hver endring vist som gammel og ny tekst og godkjent én og én.
- Gjenopprettingspunkt: tagen `v0.1-for-vercel-hosting` på main (`71164b2`). Arbeidet er gjort på egen branch `change/vercel-hosting` (laget fra `story/1-2-registration-login`).
- Endringsforslag: [`sprint-change-proposal-2026-11-01.md`](../../_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-01.md).

### Resultat
- Beslutninger: Vercel Services (frontend og FastAPI på samme domene), Neon framfor Supabase (Supabase settes på pause etter 7 dager), Neon-branch per PR-preview som slettes når PR-en lukkes (fallback: bare main migrerer), privat Vercel Blob via backend for fotobevis, daglig morgenvarsel via Vercel Cron (OQ-2 lukket), og AD-7 på samme domene uten CORS.
- Commits per dokument: PRD `9dee99b`, arkitektur `433c0e7`, UX `973c81d`, epics `a920d00`, sprint-status `4e01320`, epic-1-context `595a281`, brief `461bce7`, KI-logg `db5ec0f`, CLAUDE.md `de11560`. Endringsforslaget er committet med `status: approved`.
- Story 1.7 er ny (issue #6) og skal bygges før 1.2. Issue #5 er oppdatert til ny AD-7.
- Sjekken av om noe var glemt fant at `epic-1-context.md` var utdatert (gammel AD-7, manglet 1.7), og at FR-13 måtte begrenses til hele døgn.

### Åpne punkter
- Story 1.7: koble Neon til Vercel-prosjektet, sette Root Directory til repo-roten og eventuelt legge inn `NEON_API_KEY` som repo-secret. Bare eieren (Eirik) kan gjøre dette.
- Story 1.2: sjekke om Safari godtar `Secure`-cookie på `http://localhost`.
- Story 4.3 (Trinn 2): sjekke om privat Vercel Blob har signerte lenker, og hva overwrite-parameteren heter i Python-SDK-et.
