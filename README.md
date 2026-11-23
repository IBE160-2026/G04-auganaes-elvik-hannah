# Husly – IBE160 G04

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

Repoet inneholder gruppens applikasjon og dokumentasjon av utvikling, testing og kvalitetssikring med KI.

## Hva er Husly

**Husly** er en nettapp (PWA) for å holde orden på de uregelmessige oppgavene i et felles hjem, som å rense sluket, avkalke vannkokeren eller vaske stekeovnen. Slike oppgaver har ingen fast rytme, og blir glemt til noen blir irritert eller det dukker opp mugg.

- **For hvem:** de som deler en husstand (kollektiv, par, familie), og utleiere med leietakere. Appen er laget for mobil, men virker like godt på større skjermer.
- **Hjem og oppgaver:** et hjem har en liste med oppgaver som er **Må** eller **Bør**, med anbefalt hyppighet. Oppgavene krysses av, og neste frist regnes fra den dagen de faktisk ble gjort.
- **Tre roller:** husstandsmedlemmer er likestilte og kan opprette, endre og invitere. I et utleiehjem setter **utleier** og låser Må-oppgaver og hyppighet, og **leietaker** kan krysse av, men ikke endre det utleier har bestemt. Rollene håndheves av serveren, ikke bare av knapper som er skjult.
- **Varsler:** daglige påminnelser på mobilen (push) om det som er forfalt, en melding fra utleier til leietakerne og en rettferdig påminnelse til den som ikke har gjort sin del.
- **Utleier:** kan kreve et bilde som bevis på bestemte Må-oppgaver, og ser en portefølje over alle utleiehjemmene sine.
- **KI:** «Spør KI» på en oppgave gir et kort svar (og en chat med hjelperen «Fiks»), og leietakere får en velkomstguide. KI-en får bare oppgavenavn, oppgavetype og spørsmålet ditt, aldri navn eller e-post, og svarene har en ansvarsfraskrivelse.

Planleggingsdokumentene (brief, PRD, UX, arkitektur og epics) ligger i [`_bmad-output/planning-artifacts/`](_bmad-output/planning-artifacts/). Appen kjører lokalt uten noen kontoer eller nøkler, se [Kjøre appen lokalt](#kjøre-appen-lokalt).

**Nettversjon (valgfri):** <https://g04husly.vercel.app>. Hovedveien for å kjøre og vurdere appen er lokal kjøring, se under. Mer om nettversjonen står i [Nettversjon (valgfri)](#nettversjon-valgfri).

## Medlemmer

- Eirik Auganæs
- Steffen Elvik
- Hannah Linnea Elvestad Mattsson (har avsluttet studiet)

Eirik og Steffen har programmert sammen fra Eiriks maskin på ukentlige samlinger, så mange av commitene til begge står under Eirik.

## Dokumentasjon

- [Planleggingsdokumenter (BMAD)](_bmad-output/planning-artifacts/): product brief, PRD, UX, arkitektur og epics
- [KI-logg](docs/ki-logg/README.md): prompts fra alle KI-økter, koblet til commits
- [Eksempler på styring og korrigering av KI](docs/ki-logg/korrigeringer.md)
- [Sensorveiledning, del 1](docs/sensorveiledning.md): kriteriene vi jobber etter
- [Prøv funksjonene](docs/prov-appen.md): oppskrifter for å prøve hver funksjon i appen lokalt

## Kjøre appen lokalt

Appen kjører helt lokalt, uten gruppens kontoer eller nøkler (FR-22, AD-15). Kommandoene fungerer i zsh (macOS) og Git Bash (Windows).

> **Windows:** Kjør alle kommandoene i **Git Bash**, ikke PowerShell. Windows PowerShell 5.1 støtter ikke `&&`, og standard kjøringspolicy blokkerer `npm.ps1`. Unntaket er installasjonskommandoene under «Forutsetninger», som kjøres i PowerShell.

### Forutsetninger

Du trenger Git, Docker Desktop, uv og Node.js 24. Installer alt med én kommando:

**Windows** (åpne PowerShell som vanlig bruker, og kjør:)

```powershell
winget install --id Git.Git -e; winget install --id Docker.DockerDesktop -e; winget install --id astral-sh.uv -e; winget install --id OpenJS.NodeJS.LTS -e
wsl --install --no-distribution
```

Start deretter maskinen på nytt, start Docker Desktop og vent til den sier at den kjører (du trenger ikke logge inn i Docker). Bruk **Git Bash** til alle kommandoene videre.

**macOS** (krever [Homebrew](https://brew.sh)):

```bash
brew install git uv node@24 && brew install --cask docker
```

Start Docker Desktop fra Programmer og vent til den kjører. Hvis `node --version` ikke viser 24 etterpå, kjør `brew link --overwrite node@24`.

Lukk terminalen og åpne en ny etter installasjonen, og sjekk:

```bash
git --version && docker --version && uv --version && node --version
```

Hva de er til, og hva du gjør uten pakkehåndterer:

- **Docker Desktop** kjører databasen. Det må være startet før du kjører kommandoene. Last ned fra <https://www.docker.com/products/docker-desktop/>. På Windows må WSL2 og virtualisering være på; se «Hvis noe feiler» hvis Docker ikke starter.
- **uv** er Python-pakkehåndtereren. Den henter selv riktig Python (3.12), så du trenger ikke installere Python. Uten winget eller brew: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) eller `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows).
- **Node.js 24 LTS** (22.22.2+, 24.15+ og 26+ godtas av avhengighetene, men `frontend/.nvmrc` og CI bruker 24, og frontend-testene skal kjøres på 24). Uten winget eller brew: last ned LTS-installasjonsfilen fra <https://nodejs.org>. Feil versjon og `npm test` som henger på Node 26.7 står under «Hvis noe feiler».

### Rask start

Når forutsetningene over er på plass og Docker Desktop kjører. Åpne to terminaler (Git Bash på Windows).

Terminal 1, fra rotmappen:

```bash
docker compose up -d --wait
cd backend && uv sync && uv run python -m app.seed && uv run fastapi dev
```

Terminal 2, fra rotmappen:

```bash
cd frontend && npm ci && npm run dev
```

Åpne <http://localhost:5173> og logg inn som `mari@example.com` med passordet `husly-demo`. Går noe galt, se [Hvis noe feiler](#hvis-noe-feiler). Stegene under forklarer hver kommando, og testene står under [Tester og lint](#tester-og-lint).

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

`uv run python -m app.seed` er én kommando for både migreringer og eksempeldata (Story 1.6): den kjører `alembic upgrade head` og lager eksempelbrukerne under, eksempelhjemmene de bor i (Story 1.3 og 1.4) og åtte oppgaver i hvert av hjemmene (Story 2.1). Oppgavene settes opp som om det skjedde for noen uker siden, så noen er forfalt og noen forfaller snart. Den kan kjøres så mange ganger du vil, og sletter eller overskriver aldri noe; finnes en bruker fra før, skriver den «finnes allerede». Kjøres den før databasen er startet, avslutter den med en melding om å kjøre `docker compose up -d --wait`. Kjør den fra `backend/`.

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
2. Logg inn som Mari. Du havner på oppgaveoversikten for «Mari og Jonas sitt hjem» (`/hjem/<id>`), med de åtte oppgavene (Må-oppgavene først) og fanelinja **Oppgaver** / **Innstillinger** nederst. Last siden på nytt; du er fortsatt logget inn.
3. Gå til **Innstillinger** og trykk **Logg ut**, velg **Opprett konto** og lag din egen bruker (e-post, navn og et passord på minst 8 tegn). Uten et hjem blir du sendt til **Opprett hjemmet ditt**.
4. Velg **Husstand** eller **Utleiebolig**, gi hjemmet et navn og trykk **Opprett hjem**. Du kommer til **Sett opp oppgaver** (se [«Prøv oppgaveoppsett»](docs/prov-appen.md#prøv-oppgaveoppsett-story-21)). Med en husstand blir du husstandsmedlem; nye medlemmer kommer inn via invitasjon (Story 1.4). Med en utleiebolig blir du utleier. Hjemmene dine står under **Dine hjem** på **Innstillinger**. Regelen for å opprette flere hjem med **Opprett nytt hjem** er den samme som for å bli med (Story 1.9): en utleiebolig kan alle opprette, når som helst. En husstand kan du bare opprette når du ikke allerede er husstandsmedlem eller leietaker et annet sted. Prøver du likevel, svarer serveren «Du er allerede med i «X». Du kan bare være med i ett hjem om gangen.», og ingenting blir lagret.
5. **Logg ut** (på **Innstillinger**, eller på **Opprett hjemmet ditt** for en bruker uten hjem) sender deg tilbake til innloggingen.

**Prøv resten:** Oppskrifter for hver funksjon (invitasjon, oppgaver, avkrysning, portefølje, slett konto og flere) står i [`docs/prov-appen.md`](docs/prov-appen.md).

### Hvis noe feiler

| Symptom | Trolig årsak | Løsning |
|---|---|---|
| Docker Desktop starter ikke, eller sier at virtualisering er av («Virtualization support not detected», «WSL 2 installation is incomplete») | Virtualisering (Intel VT-x, AMD-V/SVM) er slått av i BIOS/UEFI, eller WSL2 mangler | Kjør `wsl --install --no-distribution` i PowerShell og start maskinen på nytt. Hjelper ikke det: start maskinen på nytt, gå inn i BIOS/UEFI (ofte `F2`, `F10`, `Del` eller `Esc` under oppstart; tastene varierer mellom produsenter), slå på **Virtualization Technology** (også kalt Intel VT-x, SVM Mode eller AMD-V), lagre og start på nytt. Sjekk i Oppgavebehandling → Ytelse → CPU at «Virtualisering» står som «Aktivert». |
| `docker compose` svarer at den ikke får kontakt med Docker | Docker Desktop er ikke startet | Start Docker Desktop, vent til den sier at den kjører, og kjør `docker compose up -d --wait` på nytt. |
| Seed eller backend får ikke kontakt med databasen, eller <http://localhost:8000/api/health/db> svarer ikke `{"database":"ok"}` | Databasen kjører ikke | Kjør `docker compose ps` fra rotmappen. Står ikke `db` som kjørende, kjør `docker compose up -d --wait`. Er en annen tjeneste på port 5433, avslutt den først. |
| `uv: command not found` rett etter installasjonen | Terminalen kjenner ikke uv ennå | Lukk terminalen og åpne en ny (på Windows: åpne Git Bash på nytt). |
| `&&` eller `npm.ps1` feiler på Windows | Du kjører i PowerShell | Bruk **Git Bash** for alle kommandoer unntatt installasjonen under «Forutsetninger». |
| `npm ci` viser «EBADENGINE», eller `npm run dev` feiler rett etter oppstart | For gammel Node | Sjekk `node --version` mot kravet under Forutsetninger. Installer Node 24: på macOS `nvm install` og `nvm use` i `frontend/` (`.nvmrc` peker på 24), på Windows `nvm use 24` med nvm-windows, eller installer fra nodejs.org. |
| `npm test` stopper med «Timeout waiting for worker to respond» | Node 26.7 med vitest 5.0.5 | Bytt til Node 24 og kjør på nytt. |
| Innlogging avvises for en av testbrukerne | Seed er ikke kjørt, eller databasen er ny og tom | Kjør `uv run python -m app.seed` i `backend/`. Testbrukerne bruker passordet `husly-demo`. |
| Siden åpner, men innlogging eller data feiler, og <http://localhost:5173/api/health> svarer ikke `{"status":"ok"}` | Backend kjører ikke på port 8000 | Start `uv run fastapi dev` i `backend/`, og se at porten ikke er brukt av noe annet. |
| «Slå på varsler» sier at varsler ikke støttes | Service workeren registreres bare i produksjonsbygg, og på iPhone må appen åpnes fra Hjem-skjermen | Kjør `npm run build && npm run preview` i `frontend/` og åpne <http://localhost:4173>. På iPhone legger du appen på Hjem-skjermen og åpner den derfra, ikke fra Safari. |
| Du vil begynne på nytt med tom database | | `docker compose down -v`, deretter `docker compose up -d --wait` og `uv run python -m app.seed`. |

### Tester og lint

Testene trenger verken Docker, nettverk eller nøkler; de stopper enhver nettverkstilkobling som ikke går til maskinen selv, og sjekker at `.env.example` lister nøyaktig de variablene appen leser. De samme sjekkene kjører automatisk på hver PR og på `main` i GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)), sammen med seed-kommandoen (to ganger, med sjekk av at det blir nøyaktig fire brukere, to hjem, fire medlemskap, én invitasjonslenke og 16 oppgaver, og at ingen hjem blander roller: et husstandshjem har bare husstandsmedlemmer, en utleiebolig nøyaktig én utleier og ellers bare leietakere) og migreringene opp og ned mot Postgres 18, en sjekk av at den genererte API-klienten er oppdatert, og `npm run build`.

```bash
cd backend
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Samtidighetstestene i `backend/tests/postgres/` (radlåsene i `create_home`, `invites.accept`, `add_member`, `set_up_tasks`, `adjust_task`, bildeopplasting, kontosletting og migreringslåsen) trenger en ekte Postgres, siden SQLite ignorerer `FOR UPDATE`. De hoppes over uten `HUSLY_POSTGRES_TEST_URL`, så `uv run pytest` er uendret. CI kjører dem mot Postgres 18. Lokalt: `docker compose up -d --wait`, så

```bash
cd backend
HUSLY_POSTGRES_TEST_URL=postgresql+psycopg://husly:husly@localhost:5433/postgres uv run pytest tests/postgres -v
```

Hver testmodul lager og migrerer sin egen database (`husly_conc_…`) på serveren og sletter den etterpå; `husly`-databasen røres ikke.

```bash
cd frontend
npm test -- --run
npm run lint
```

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
    routes/          tynt HTTP-lag (/api/health, /api/auth/*, /api/homes, /api/task-types)
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
    components/      AppShell, PrimaryButton, TextField, InstallPrompt, Badge
    routes/          sider: logg inn, registrer, opprett hjem, oppgaveoppsett, hjemside
    api/             generert API-klient, økt i minnet og TanStack Query-hooks
  openapi.json       API-skjemaet klienten genereres fra (npm run gen:api)
    service-worker.ts
```

## Konfigurasjon og drift

### Mock-modus og ekte nøkler

- **Mock-modus uten nøkler.** Uten nøkler svarer appen med mock, og hvert punkt under kan prøves lokalt:
  - **KI-svarene («?» på en oppgave) er mocket uten nøkkel.** Uten `GEMINI_API_KEY` svarer en mock-leverandør med ferdigskrevne, oppgavespesifikke svar, og popoveren er merket «Demo-svar». Mocken leser ikke spørsmålet du skriver.
  - **Velkomstguiden (Story 5.3)** lages for utleiehjem når oppgavene settes opp: KI skriver én gang en kort innledning (uten nøkkel: en ferdigskrevet demo-tekst), mens hjemmets navn og dagens Må-oppgaver med hyppighet leses levende og aldri sendes til KI. Oppsettet teller som ett av utleierens 20 KI-kall, og feiler KI, brukes en fast tekst. Leietakeren ser guiden som et kort øverst på oppgaveoversikten og kan skjule den; den ligger alltid under Innstillinger → «Velkomstguide» (utleier ser den også der). Prøv det: opprett et utleiehjem og sett opp oppgaver, inviter en leietaker, og åpne hjemmet som leietaker. Seed-hjemmet til Kari har ingen lagret innledning, så der vises den faste teksten.
  - Når et svar er vist, åpner «Spør mer» en chat (Story 5.2) med oppgaven som utgangspunkt; hver melding i chatten er ett KI-kall som teller blant de 20 per dag, og uten nøkkel svarer mocken på oppfølgingsspørsmål (når chatten har tidligere meldinger) med et demosvar som nevner oppgaven. Prøv det: åpne «Spør KI» på en oppgave, trykk «Spør mer» og send en oppfølging. Serveren lagrer ingen chat: den lever bare i nettleseren mens siden er åpen. Testene bruker alltid mocken. I nettversjonen på Vercel gjelder det samme: er `GEMINI_API_KEY` ikke satt der, svarer mocken.
  - **Push-varsler (Story 3.1) er mocket uten nøkler.** Uten `VAPID_PUBLIC_KEY` og `VAPID_PRIVATE_KEY` får nettleseren en fast utviklingsnøkkel, så «Slå på varsler» under Innstillinger lagrer enheten som vanlig. Forfallsjobben (Story 3.2) sender da ikke på ekte: en mock-avsender logger hva den ville sendt. Kjør jobben for hånd med `curl http://localhost:8000/api/internal/run-due-check` (uten `CRON_SECRET` og uten VAPID-nøkler trengs ingen hemmelighet; porten er den `fastapi dev` bruker hos deg). Svaret sier hvor mange medlemmer, oppgaver og push den fant. Samme dag gir et nytt kall ingenting nytt, siden hver oppgave og hvert medlem bare varsles én gang per dag.
  - **Utleiers melding til leietakerne (Story 3.4)** går samme vei: uten VAPID-nøkler logger mock-avsenderen at den ville sendt, men siden holder ingen enhet tilbake, sier utleiersiden likevel «Sendt til N leietakere» (også i nettversjonen på Vercel til VAPID-nøklene er satt under Production). Prøv den som utleier (Kari i seed-dataene) under «Send melding til leietakerne» på oppgaveoversikten.
  - Samme side («Administrer hjemmet») har valget «Påminnelser til leietakerne» (Story 3.5): hver dag, annenhver dag eller én gang i uken for Må-oppgaver. Forfallsjobben følger det for leietakere, og fristdagen varsler alltid.
  - Se effekten lokalt: velg «Én gang i uken», opprett en Må-oppgave med frist for et par dager siden som utleier, og kjør `run-due-check` (som over) for to dager på rad; leietakeren varsles bare på fristdagen og så hver sjuende dag.
  - Samme side har «Bildebevis» (Story 4.1): utleier kan krysse av for å kreve bilde på Må-oppgaver av typer der det går an å se at det er gjort («Rens sluket» og «Rens filteret i kjøkkenviften» i katalogen). Leietakeren kan da ikke krysse av uten bilde: oppgaven får «Last opp bilde» i stedet for avkrysning, og bildet (JPEG, maks 3,5 MB, minnes ned i nettleseren) lagres én gang per oppgave (Story 4.2). Uten `BLOB_READ_WRITE_TOKEN` ligger bildene i mappen `backend/.photo-evidence` (`PHOTO_STORAGE_DIR` overstyrer), som git ignorerer, så det kan prøves uten konto. Med token brukes en privat Vercel Blob-lagring. Uten token på Vercel (skrivebeskyttet disk) feiler opplasting med beskjed om at bildet ikke ble lagret, så Blob-lagringen må kobles til før den hostede demoen kan ta imot bilder.
  - Utleier ser bildet og beskrivelsen på oppgavedetaljene (Story 4.3): bildet hentes gjennom backend, aldri med en lagringsadresse, og leietakere og andre utleiere får 403. Prøv det lokalt: last opp et bilde som leietaker (se over), logg inn som utleier (Kari) og åpne oppgaven.
  - Bilder fra opplastinger på Vercel før denne rettingen finnes ikke (Blob-adapteren lagret ingenting), så utleier får «Bildet finnes ikke lenger» til leietakeren laster opp på nytt.
  - **Rettferdig påminnelse (Story 3.3):** har ett medlem gjort de tre siste fullføringene av en delt oppgave og et annet ingen, går første påminnelse om oppgaven bare til det andre medlemmet (utleier, tidligere medlemmer og medlemmer som kom etterpå teller ikke med), og dagen etter får alle den vanlige påminnelsen. Seed-dataene gir Mari tre fullføringer av «Støvsug og vask gulvene» og Jonas ingen: slå på varsler som Mari og Jonas, og kjør `run-due-check` (som over); da får bare Jonas påminnelsen om gulvene. Regelen står i `backend/app/domain/fairness.py` (`WINDOW = 3`) og testene i `backend/tests/test_fairness.py`.
  - Service workeren registreres bare i produksjonsbygg, så test varsler med `npm run build && npm run preview` (eller Docker), ikke med `npm run dev`. På iPhone (iOS 16.4 eller nyere) virker varsler bare når Husly er lagt på Hjem-skjermen og åpnes fra ikonet, ikke fra Safari; ellers står det «Varsler støttes ikke her» under Innstillinger → Varsler (bekreftet på ekte iPhone mot Production 22.11). Andre eksterne tjenester brukes ikke i Trinn 1.
- **Egne verdier og nøkler (valgfritt):** Kopier [`.env.example`](.env.example) til `.env` i rotmappen og kjør backend-kommandoene med `--env-file ../.env` etter `uv run` (f.eks. `uv run --env-file ../.env fastapi dev`). `.env` kan overstyre `DATABASE_URL`, `JWT_SECRET`, `AUTH_COOKIE_SECURE` og, for ekte KI-svar, `GEMINI_API_KEY` (og valgfritt `GEMINI_MODEL`), og for ekte push `VAPID_PUBLIC_KEY` og `VAPID_PRIVATE_KEY` (valgfritt `VAPID_SUBJECT`).
  - `CRON_SECRET` beskytter forfallsjobben: på Vercel, og når ekte VAPID-nøkler er satt, avvises alle kall uten `Authorization: Bearer <CRON_SECRET>`.
  - Vercel Cron kaller den hver dag klokken 06:00 UTC (`vercel.json`), og bare i Production-deployen: legg `CRON_SECRET` inn under Production i Vercel, ellers avvises Crons kall.
  - Settes nøkkelen, sendes bare oppgavenavnet, katalogtypen og spørsmålet ditt til Google Gemini (i chatten også dine tidligere spørsmål og KI-ens svar på dem), aldri navn, e-post eller hjemmenavn.
  - Hver bruker kan stille 20 KI-spørsmål per dag (UTC-døgn); den 21. får beskjed om når grensen nullstilles. Kall som feiler eller går over 10 sekunder teller også, og mock-svar teller.
  - Nye nøkler legges i `.env.example` av storyen som trenger dem. `.env` er ignorert av git og skal aldri committes.
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

### Porter

| Tjeneste | Port |
|---|---|
| PostgreSQL (Docker) | 5433 (5432 inne i containeren, så den ikke kolliderer med en lokal PostgreSQL) |
| Backend (FastAPI) | 8000 |
| Frontend, utvikling (`npm run dev`) | 5173 |
| Frontend, produksjonsbygg (`npm run preview`) | 4173 |

## Nettversjon (valgfri)

<https://g04husly.vercel.app> er en demo av den samme koden. Den trengs ikke for å kjøre, teste eller vurdere appen. Alt over fungerer uten den.

- **Oppsett:** Ett Vercel-prosjekt (`g04husly`) med `frontend/` og `backend/` som Vercel Services på samme domene ([`vercel.json`](vercel.json)). Alt under `/api` går til FastAPI, resten til React-appen. Databasen er Neon Postgres 18 i EU (Frankfurt), koblet til gjennom Vercels Neon-integrasjon, som setter `DATABASE_URL` og `DATABASE_URL_UNPOOLED`. `JWT_SECRET` (minst 32 byte) er satt for Production og Preview i prosjektinnstillingene; uten den starter ikke API-et på Vercel. React-appen får `index.html` for alle stier som ikke er filer, så lenker som `/logg-inn` fungerer direkte.
- **Oppdatering:** `main` publiseres automatisk. Hver PR får en egen forhåndsvisning med sin egen Neon-gren (`preview/<git-gren>`), som slettes når PR-en lukkes ([workflow](.github/workflows/neon-preview-cleanup.yml)).
- **Migreringer:** `alembic upgrade head` kjører i backendens byggesteg (`[tool.vercel.scripts]` i `backend/pyproject.toml`). En feilende migrering stopper bygget, så forrige versjon blir stående. En migrering som allerede er committet, blir likevel liggende i databasen selv om et senere byggesteg feiler, så migreringer må være bakoverkompatible med forrige versjon av koden.
- **Sjekk:** `/api/health` svarer at API-et lever, og `/api/health/db` at det når databasen.
- **Tilgang:** Bare prosjekteieren (Eirik) ser Vercel- og Neon-dashboardene. Ingen nøkler ligger i repoet; de står bare i Vercel- og GitHub-innstillingene.
- **Tilbakerulling:** Hvis Services-oppsettet må forlates, går vi tilbake til taggen `v0.1-for-vercel-hosting` (bare frontenden på Vercel): sett Root Directory til `frontend` og Framework Preset til **Vite** i prosjektinnstillingene.
