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
uv run python -m app.seed
uv run fastapi dev
```

`uv run python -m app.seed` er én kommando for både migreringer og eksempeldata (Story 1.6): den kjører `alembic upgrade head` og lager eksempelbrukerne under og eksempelhjemmene de bor i (Story 1.3 og 1.4). Den kan kjøres så mange ganger du vil, og sletter eller overskriver aldri noe; finnes en bruker fra før, skriver den «finnes allerede». Kjøres den før databasen er startet, avslutter den med en melding om å kjøre `docker compose up -d --wait`. Kjør den fra `backend/`.

API-et kjører på <http://localhost:8000>. Sjekk at det svarer: <http://localhost:8000/api/health> skal gi `{"status":"ok"}`, og <http://localhost:8000/api/health/db> skal gi `{"database":"ok"}` når databasen kjører. API-dokumentasjon ligger på <http://localhost:8000/docs>.

Ingen `.env` trengs: standardverdiene matcher `docker-compose.yml`, og uten `JWT_SECRET` bruker backenden en fast nøkkel for lokal utvikling (den logger en advarsel om det). Variablene står i [`.env.example`](.env.example). Vil du overstyre dem, kopierer du filen til `.env` og legger til `--env-file ../.env` etter `uv run`.

### 3. Frontend

I et nytt terminalvindu:

```bash
cd frontend
npm ci
npm run dev
```

Appen åpnes på <http://localhost:5173>. Frontenden kaller API-et på samme adresse: Vite sender alt under `/api` videre til backenden på port 8000, både i `npm run dev` og `npm run preview`. <http://localhost:5173/api/health> skal derfor også gi `{"status":"ok"}` når backenden kjører.

### 4. Første innlogging

Seed-kommandoen lager disse eksempelbrukerne:

| Navn | E-post | Passord | Hjem (rolle) |
|---|---|---|---|
| Mari Nordmann | `mari@example.com` | `husly-demo` | «Mari og Jonas sitt hjem», husstand (husstandsmedlem) |
| Jonas Berg | `jonas@example.com` | `husly-demo` | «Mari og Jonas sitt hjem», husstand (husstandsmedlem) |
| Kari Hansen | `kari@example.com` | `husly-demo` | «Storgata 12», utleiebolig (utleier) |
| Anders Johnsen | `anders@example.com` | `husly-demo` | «Storgata 12», utleiebolig (leietaker, kom inn via en invitasjonslenke) |

1. Åpne <http://localhost:5173>. Du blir sendt til **Logg inn**.
2. Logg inn som Mari. Du havner på hjemsiden for «Mari og Jonas sitt hjem», med type og rolle. Last siden på nytt; du er fortsatt logget inn.
3. **Logg ut**, velg **Opprett konto** og lag din egen bruker (e-post, navn og et passord på minst 8 tegn). Uten et hjem blir du sendt til **Opprett hjemmet ditt**.
4. Velg **Husstand** eller **Utleiebolig**, gi hjemmet et navn og trykk **Opprett hjem**. Med en husstand blir du husstandsmedlem og får ikke tilbud om å lage flere hjem; nye medlemmer kommer inn via invitasjon (Story 1.4). Med en utleiebolig blir du utleier, ser listen over hjemmene dine og kan lage flere med **Opprett nytt hjem**.
5. **Logg ut** sender deg tilbake til innloggingen.

**Prøv invitasjon (Story 1.4):**

1. Logg inn som Mari og velg **Medlemmer og invitasjon** på hjemsiden. Trykk **Lag invitasjonslenke**. Lenken kan brukes én gang og gjelder i 7 dager; **Lag ny lenke** lager en til, og de gamle virker fortsatt.
2. Åpne lenken i et privat vindu. Du ser hjemmet og rollen. Velg **Opprett konto og bli med** og lag en ny bruker. Du er da med i «Mari og Jonas sitt hjem» som husstandsmedlem.
3. Logg ut (private vinduer i samme nettleser deler innlogging), eller bruk en annen nettleser, og åpne den samme lenken igjen. Nå står det at lenken ikke lenger er gyldig.
4. Logg inn som Anders (leietaker) og åpne **Medlemmer og invitasjon**: der er det ingen knapp for å invitere. Serveren nekter også, hvis han prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `anders@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Kjør `GET /api/homes` og kopier `id` til «Storgata 12».
   4. Kjør `POST /api/homes/{home_id}/invites` med den `id`-en. Svaret er 403.
5. Er du allerede husstandsmedlem eller leietaker i ett hjem, kan du ikke bli med i et annet; invitasjonssiden sier fra om det. En utleier kan i tillegg bli med i ett slikt hjem.

Innloggingen fungerer også i Safari på `http://localhost`, fordi cookien bare får `Secure` på Vercel (eller med `AUTH_COOKIE_SECURE=true`).

### Mock-modus og ekte nøkler

- **Ingenting er mocket ennå.** Trinn 1 bruker ingen eksterne tjenester, så appen trenger ingen nøkler, og det finnes ingen mock-modus å vise. Fra Story 5.1 (KI-forslag) brukes en mock automatisk når nøkkelen mangler, og KI-svarene merkes da «demo-modus» i appen. Testene bruker alltid mockene.
- **Egne verdier og nøkler (valgfritt):** Kopier [`.env.example`](.env.example) til `.env` i rotmappen og kjør backend-kommandoene med `--env-file ../.env` etter `uv run` (f.eks. `uv run --env-file ../.env fastapi dev`). I dag kan `.env` bare overstyre `DATABASE_URL`, `JWT_SECRET` og `AUTH_COOKIE_SECURE`. Nye nøkler, som `GEMINI_API_KEY` fra Story 5.1, legges i `.env.example` av storyen som trenger dem. `.env` er ignorert av git og skal aldri committes.
- **Seed-kommandoen skriver bare til en lokal database.** Den nekter å kjøre på Vercel, og når `DATABASE_URL` eller `DATABASE_URL_UNPOOLED` (også fra `.env`) peker til en annen maskin enn `localhost`/`127.0.0.1`/`::1`, uten å skrive noe (exit 2; exit 1 betyr at databasen ikke svarer). Eksempelbrukerne med kjente passord havner derfor aldri i nettversjonen; der registrerer du din egen konto.

### Når API-et endres

Frontenden har en typet API-klient generert fra FastAPIs OpenAPI-skjema. Etter en endring i backendens ruter eller modeller:

```bash
cd backend && uv run python -m app.export_openapi   # skriver frontend/openapi.json
cd ../frontend && npm run gen:api                   # skriver src/api/schema.d.ts
```

Commit begge filene. En test i backenden og et steg i CI feiler hvis de ikke er oppdatert.

### Sjekke PWA-en (manifest og service worker)

Service workeren registreres bare i produksjonsbygget:

```bash
cd frontend
npm run build && npm run preview
```

Åpne <http://localhost:4173>, og gå til DevTools → Application. Der skal manifestet være gyldig, og `/service-worker.js` skal være aktiv med scope `/`.

### Tester og lint

Testene trenger verken Docker, nettverk eller nøkler; de stopper enhver nettverkstilkobling som ikke går til maskinen selv, og sjekker at `.env.example` lister nøyaktig de variablene appen leser. De samme sjekkene kjører automatisk på hver PR og på `main` i GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)), sammen med seed-kommandoen (to ganger, med sjekk av at det blir nøyaktig fire brukere, to hjem, fire medlemskap og én invitasjonslenke) og migreringene opp og ned mot Postgres 18, en sjekk av at den genererte API-klienten er oppdatert, og `npm run build`.

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
    config.py        leser miljøvariablene (DATABASE_URL, JWT_SECRET, AUTH_COOKIE_SECURE)
    db.py            databasemotor, én per URL
    routes/          tynt HTTP-lag (/api/health, /api/auth/*, /api/homes)
    domain/          domenetjenester, eneste vei for endringer (AD-3)
    permissions/     innlogget bruker og rolle-sjekker (AD-2)
    models/          SQLModel-entiteter
    seed/            seed-kommandoen: migreringer og eksempeldata (python -m app.seed)
  alembic/           databasemigreringer
  tests/             pytest
frontend/            React 19 + TypeScript + Vite
  public/            manifest.json og app-ikoner (AD-12)
  src/
    styles/          designtokens fra DESIGN.md og globale stiler (AD-13)
    components/      AppShell, PrimaryButton, TextField, InstallPrompt
    routes/          sider: logg inn, registrer, opprett hjem, hjemside
    api/             generert API-klient, økt i minnet og TanStack Query-hooks
  openapi.json       API-skjemaet klienten genereres fra (npm run gen:api)
    service-worker.ts
```

## Nettversjon (valgfri)

<https://g04husly.vercel.app> er en demo av den samme koden. Den trengs ikke for å kjøre, teste eller vurdere appen. Alt over fungerer uten den.

- **Oppsett:** Ett Vercel-prosjekt (`g04husly`) med `frontend/` og `backend/` som Vercel Services på samme domene ([`vercel.json`](vercel.json)). Alt under `/api` går til FastAPI, resten til React-appen. Databasen er Neon Postgres 18 i EU (Frankfurt), koblet til gjennom Vercels Neon-integrasjon, som setter `DATABASE_URL` og `DATABASE_URL_UNPOOLED`. `JWT_SECRET` (minst 32 byte) er satt for Production og Preview i prosjektinnstillingene; uten den starter ikke API-et på Vercel. React-appen får `index.html` for alle stier som ikke er filer, så lenker som `/logg-inn` fungerer direkte.
- **Oppdatering:** `main` publiseres automatisk. Hver PR får en egen forhåndsvisning med sin egen Neon-gren (`preview/<git-gren>`), som slettes når PR-en lukkes ([workflow](.github/workflows/neon-preview-cleanup.yml)).
- **Migreringer:** `alembic upgrade head` kjører i backendens byggesteg (`[tool.vercel.scripts]` i `backend/pyproject.toml`). En feilende migrering stopper bygget, så forrige versjon blir stående. En migrering som allerede er committet, blir likevel liggende i databasen selv om et senere byggesteg feiler, så migreringer må være bakoverkompatible med forrige versjon av koden.
- **Sjekk:** `/api/health` svarer at API-et lever, og `/api/health/db` at det når databasen.
- **Tilgang:** Bare prosjekteieren (Eirik) ser Vercel- og Neon-dashboardene. Ingen nøkler ligger i repoet; de står bare i Vercel- og GitHub-innstillingene.
- **Tilbakerulling:** Hvis Services-oppsettet må forlates, går vi tilbake til taggen `v0.1-for-vercel-hosting` (bare frontenden på Vercel): sett Root Directory til `frontend` og Framework Preset til **Vite** i prosjektinnstillingene.
