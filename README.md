# G04 — EHS

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

Repoet inneholder gruppens applikasjon og dokumentasjon av utvikling, testing og kvalitetssikring med KI.

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

Starter PostgreSQL 17 på port **5433** og venter til databasen er klar. Data ligger i Docker-volumet `husly-db`. Stopp med `docker compose down` (legg til `-v` for å slette dataene).

### 2. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev
```

API-et kjører på <http://localhost:8000>. Sjekk at det svarer: <http://localhost:8000/api/health> skal gi `{"status":"ok"}`. API-dokumentasjon ligger på <http://localhost:8000/docs>.

Ingen `.env` trengs: standardverdiene matcher `docker-compose.yml`. Variablene står i [`.env.example`](.env.example). Vil du overstyre dem, kopierer du filen til `.env` og legger til `--env-file ../.env` etter `uv run`.

### 3. Frontend

I et nytt terminalvindu:

```bash
cd frontend
npm ci
npm run dev
```

Appen åpnes på <http://localhost:5173>.

### Sjekke PWA-en (manifest og service worker)

Service workeren registreres bare i produksjonsbygget:

```bash
cd frontend
npm run build && npm run preview
```

Åpne <http://localhost:4173>, og gå til DevTools → Application. Der skal manifestet være gyldig, og `/service-worker.js` skal være aktiv med scope `/`.

### Tester og lint

Testene trenger verken Docker, nettverk eller nøkler.

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
docker-compose.yml   lokal PostgreSQL (AD-15)
.env.example         alle miljøvariabler, uten hemmeligheter
backend/             FastAPI + SQLModel + Alembic (Python 3.12, uv)
  app/
    main.py          app-oppsett, CORS og ruter under /api
    config.py        leser DATABASE_URL og CORS_ORIGINS
    routes/          tynt HTTP-lag (foreløpig bare /api/health)
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
