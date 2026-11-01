# G04 — EHS

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

Repoet inneholder gruppens applikasjon og dokumentasjon av utvikling, testing og kvalitetssikring med KI.

**Nettversjon (valgfri):** <https://g04husly.vercel.app>. Hovedveien for å kjøre og vurdere appen er lokal kjøring, se under. Mer om nettversjonen står i [Nettversjon (valgfri)](#nettversjon-valgfri).

## Medlemmer

- Eirik Auganæs
- Steffen Elvik
- Hannah Linnea Elvestad Mattsson

## Dokumentasjon

- [Planleggingsdokumenter (BMAD)](_bmad-output/planning-artifacts/): product brief, PRD, UX, arkitektur og epics
- [KI-logg](docs/ki-logg/README.md): prompts fra alle KI-økter, koblet til commits
- [Eksempler på styring og korrigering av KI](docs/ki-logg/korrigeringer.md)
- [Sensorveiledning, del 1](docs/sensorveiledning.md): kriteriene vi jobber etter

## Kjøre appen lokalt

Appen kjører helt lokalt, uten gruppens kontoer eller nøkler (FR-22, AD-15). Kommandoene fungerer i zsh (macOS) og Git Bash (Windows).

> **Windows:** Kjør alle kommandoene i **Git Bash**, ikke PowerShell. Windows PowerShell 5.1 støtter ikke `&&`, og standard kjøringspolicy blokkerer `npm.ps1`. Unntaket er installasjonskommandoen for uv nedenfor, som er laget for PowerShell.

### Forutsetninger

- **Docker Desktop**, og det må være startet før du kjører kommandoene. På Windows må WSL2 være slått på (Docker Desktop spør om dette ved installasjon).
- **uv** (Python-pakkehåndterer). uv henter selv riktig Python-versjon (3.12), så du trenger ikke installere Python.
  - macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh` (eller `brew install uv`)
  - Windows: `winget install astral-sh.uv`, eller i PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. Åpne Git Bash på nytt etterpå.
- **Node.js 22.22.2+, 24.15+ eller 26+** (`^22.22.2 || ^24.15.0 || >=26.0.0`, det strengeste kravet blant avhengighetene, fra jsdom). `frontend/.nvmrc` peker på 24 LTS. Sjekk med `node --version`.

### 1. Database

Fra rotmappen:

```bash
docker compose up -d --wait
```

Starter PostgreSQL 18 på port **5433** og venter til databasen er klar. Data ligger i Docker-volumet `husly-db-18`. Stopp med `docker compose down` (legg til `-v` for å slette dataene).

> **Hadde du databasen fra før (PostgreSQL 17)?** Den lå i volumet `husly-db`, som 18 ikke kan bruke. Du får en ny, tom database automatisk. Det gamle volumet kan slettes: finn navnet med `docker volume ls --filter name=husly-db` (det heter f.eks. `prosjektoppgave_husly-db`) og slett det med `docker volume rm <navn>`.

### 2. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev
```

API-et kjører på <http://localhost:8000>. Sjekk at det svarer: <http://localhost:8000/api/health> skal gi `{"status":"ok"}`, og <http://localhost:8000/api/health/db> skal gi `{"database":"ok"}` når databasen kjører. API-dokumentasjon ligger på <http://localhost:8000/docs>.

Ingen `.env` trengs: standardverdiene matcher `docker-compose.yml`. Variablene står i [`.env.example`](.env.example). Vil du overstyre dem, kopierer du filen til `.env` og legger til `--env-file ../.env` etter `uv run`.

### 3. Frontend

I et nytt terminalvindu:

```bash
cd frontend
npm ci
npm run dev
```

Appen åpnes på <http://localhost:5173>. Frontenden kaller API-et på samme adresse: Vite sender alt under `/api` videre til backenden på port 8000, både i `npm run dev` og `npm run preview`. <http://localhost:5173/api/health> skal derfor også gi `{"status":"ok"}` når backenden kjører.

### Sjekke PWA-en (manifest og service worker)

Service workeren registreres bare i produksjonsbygget:

```bash
cd frontend
npm run build && npm run preview
```

Åpne <http://localhost:4173>, og gå til DevTools → Application. Der skal manifestet være gyldig, og `/service-worker.js` skal være aktiv med scope `/`.

### Tester og lint

Testene trenger verken Docker, nettverk eller nøkler. De samme sjekkene kjører automatisk på hver PR og på `main` i GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)), sammen med `alembic upgrade head` mot Postgres 18 og `npm run build`.

```bash
cd backend
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

```bash
cd frontend
npm test -- --run
npm run lint
```

### Porter

| Tjeneste | Port |
|---|---|
| PostgreSQL (Docker) | 5433 (5432 inne i containeren, så den ikke kolliderer med en lokal PostgreSQL) |
| Backend (FastAPI) | 8000 |
| Frontend, utvikling (`npm run dev`) | 5173 |
| Frontend, produksjonsbygg (`npm run preview`) | 4173 |

## Mappestruktur

```text
docker-compose.yml   lokal PostgreSQL 18 (AD-15)
.env.example         alle miljøvariabler, uten hemmeligheter
vercel.json          nettversjonen: frontend og backend som Vercel Services (Story 1.7)
.github/workflows/   CI (tester, lint, migreringer, bygg) og sletting av Neon-grenen til en PR
backend/             FastAPI + SQLModel + Alembic (Python 3.12, uv)
  app/
    main.py          app-oppsett og ruter under /api (samme origin, ingen CORS)
    config.py        leser og normaliserer DATABASE_URL (og DATABASE_URL_UNPOOLED)
    db.py            databasemotor, én per URL
    routes/          tynt HTTP-lag (foreløpig /api/health og /api/health/db)
    domain/          domenetjenester, eneste vei for endringer (AD-3)
    permissions/     rolle-sjekker (AD-2)
    models/          SQLModel-entiteter
  alembic/           databasemigreringer
  tests/             pytest
frontend/            React 19 + TypeScript + Vite
  public/            manifest.json og app-ikoner (AD-12)
  src/
    styles/          designtokens fra DESIGN.md og globale stiler (AD-13)
    components/      AppShell, PrimaryButton, InstallPrompt
    routes/          sider (fra Story 1.2)
    api/             API-klient og TanStack Query-hooks (fra Story 1.2)
    service-worker.ts
```

## Nettversjon (valgfri)

<https://g04husly.vercel.app> er en demo av den samme koden. Den trengs ikke for å kjøre, teste eller vurdere appen. Alt over fungerer uten den.

- **Oppsett:** Ett Vercel-prosjekt (`g04husly`) med `frontend/` og `backend/` som Vercel Services på samme domene ([`vercel.json`](vercel.json)). Alt under `/api` går til FastAPI, resten til React-appen. Databasen er Neon Postgres 18 i EU (Frankfurt), koblet til gjennom Vercels Neon-integrasjon, som setter `DATABASE_URL` og `DATABASE_URL_UNPOOLED`.
- **Oppdatering:** `main` publiseres automatisk. Hver PR får en egen forhåndsvisning med sin egen Neon-gren (`preview/<git-gren>`), som slettes når PR-en lukkes ([workflow](.github/workflows/neon-preview-cleanup.yml)).
- **Migreringer:** `alembic upgrade head` kjører i backendens byggesteg (`[tool.vercel.scripts]` i `backend/pyproject.toml`). En feilende migrering stopper bygget, så forrige versjon blir stående. En migrering som allerede er committet, blir likevel liggende i databasen selv om et senere byggesteg feiler, så migreringer må være bakoverkompatible med forrige versjon av koden.
- **Sjekk:** `/api/health` svarer at API-et lever, og `/api/health/db` at det når databasen.
- **Tilgang:** Bare prosjekteieren (Eirik) ser Vercel- og Neon-dashboardene. Ingen nøkler ligger i repoet; de står bare i Vercel- og GitHub-innstillingene.
- **Tilbakerulling:** Hvis Services-oppsettet må forlates, går vi tilbake til taggen `v0.1-for-vercel-hosting` (bare frontenden på Vercel): sett Root Directory til `frontend` og Framework Preset til **Vite** i prosjektinnstillingene.
