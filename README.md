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
4. Velg **Husstand** eller **Utleiebolig**, gi hjemmet et navn og trykk **Opprett hjem**. Du kommer til **Sett opp oppgaver** (se under). Med en husstand blir du husstandsmedlem; nye medlemmer kommer inn via invitasjon (Story 1.4). Med en utleiebolig blir du utleier. Hjemmene dine står under **Dine hjem** på **Innstillinger**. Regelen for å opprette flere hjem med **Opprett nytt hjem** er den samme som for å bli med (Story 1.9): en utleiebolig kan alle opprette, når som helst. En husstand kan du bare opprette når du ikke allerede er husstandsmedlem eller leietaker et annet sted. Prøver du likevel, svarer serveren «Du er allerede med i «X». Du kan bare være med i ett hjem om gangen.», og ingenting blir lagret.
5. **Logg ut** (på **Innstillinger**, eller på **Opprett hjemmet ditt** for en bruker uten hjem) sender deg tilbake til innloggingen.

**Prøv regelen for å opprette hjem (Story 1.9):** Stegene forutsetter en nyseedet database (`uv run python -m app.seed` fra `backend/` på en tom database), siden de lager nye hjem.

1. Logg inn som Kari, gå til **Innstillinger** og trykk **Opprett nytt hjem**. Hun er bare utleier, så hun får velge både **Husstand** og **Utleiebolig**. Velg **Husstand**, gi hjemmet et navn og trykk **Opprett hjem**. Hun blir husstandsmedlem i det nye hjemmet og kommer til **Sett opp oppgaver**.
2. Logg inn som Jonas, gå til **Innstillinger** og trykk **Opprett nytt hjem**. Siden heter **Opprett ny utleiebolig**, tilbyr bare utleiebolig og sier at medlemskapet hans i «Mari og Jonas sitt hjem» ikke endres. Etter at han har opprettet den, er han både husstandsmedlem der og utleier i den nye.
3. Serveren håndhever regelen selv om noen prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `jonas@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Kjør `POST /api/homes` med `{"name": "Hytta", "type": "household"}`. Svaret er 409 med «Du er allerede med i «Mari og Jonas sitt hjem». Du kan bare være med i ett hjem om gangen.», og ingenting blir lagret.
4. Jonas og Kari har nå to hjem hver, og bytter mellom dem under **Dine hjem** (se «Prøv oppgaveoversikten» under).

**Prøv invitasjon (Story 1.4):**

1. Logg inn som Mari og velg **Medlemmer og invitasjon** øverst på oppgaveoversikten. Under **Medlemmer** ser hun seg selv («(deg)») og Jonas som husstandsmedlemmer. Trykk **Lag invitasjonslenke**. Lenken kan brukes én gang og gjelder i 7 dager; **Lag ny lenke** lager en til, og de gamle virker fortsatt.
2. Åpne lenken i et privat vindu. Du ser hjemmet og rollen. Velg **Opprett konto og bli med** og lag en ny bruker. Du er da med i «Mari og Jonas sitt hjem» som husstandsmedlem.
3. Logg ut (private vinduer i samme nettleser deler innlogging), eller bruk en annen nettleser, og åpne den samme lenken igjen. Nå står det at lenken ikke lenger er gyldig.
4. Logg inn som Anders (leietaker) og åpne **Medlemmer og invitasjon** for «Storgata 12». Under **Medlemmer** ser han Kari Hansen (Utleier) og seg selv (Leietaker, «(deg)»), men ingen knapp for å invitere (Story 1.5). Serveren nekter også, hvis han prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `anders@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Kjør `GET /api/homes` og kopier `id` til «Storgata 12».
   4. Kjør `POST /api/homes/{home_id}/invites` med den `id`-en. Svaret er 403.
   5. Logg inn som Mari på samme måte og kjør `GET /api/homes/{home_id}/members` med `id`-en til «Storgata 12». Svaret er 403, fordi hun ikke er medlem der (Story 1.5).
5. Er du allerede husstandsmedlem eller leietaker i ett hjem, kan du ikke bli med i et annet; invitasjonssiden sier fra om det. Utleierroller teller ikke, så en utleier kan i tillegg bli med i ett slikt hjem. Det er den samme regelen som avgjør om du kan opprette en husstand (Story 1.9).

**Prøv å forlate et hjem (Story 1.8):**

1. Logg inn som Jonas og åpne **Medlemmer og invitasjon**. Trykk **Forlat hjemmet**. Teksten forklarer hva som skjer; ingenting er sendt ennå, og **Avbryt** tar deg tilbake. Trykk **Ja, forlat hjemmet**. Du havner på **Opprett hjemmet ditt** med beskjeden «Du har forlatt «Mari og Jonas sitt hjem».», og kan opprette et eget hjem eller bli med via en ny invitasjon.
2. Logg inn som Mari og åpne **Medlemmer og invitasjon**. Under **Medlemmer** står bare hun. Hun har ingen **Fjern**-knapp: et husstandsmedlem kan bare forlate selv.
3. Logg inn som Anders i én nettleser og åpne **Medlemmer og invitasjon** for «Storgata 12». Logg inn som Kari i en annen nettleser (eller et privat vindu), åpne samme side og trykk **Fjern** ved Anders og så **Ja, fjern Anders Johnsen**. Kari ser «Anders Johnsen er fjernet.». Bytt så til en annen fane i Anders sin nettleser (eller minimer vinduet) og tilbake, uten å laste siden på nytt: han blir sendt til **Opprett hjemmet ditt**, uten feilside. Det holder ikke å klikke mellom to vinduer som står side om side; appen henter data på nytt når fanen blir synlig igjen, ikke når vinduet får fokus. Kari har ingen **Forlat hjemmet**-knapp: en utleier kan ikke forlate sin egen utleiebolig.
4. Angre ved å kjøre `uv run python -m app.seed` fra `backend/` igjen. Den legger Jonas tilbake i «Mari og Jonas sitt hjem» og Anders tilbake i «Storgata 12» (med en ny invitasjonslenke), og sletter ingenting. Har Jonas eller Anders laget eller blitt med i et annet hjem i mellomtiden, hopper seed-en over dem.

**Prøv oppgaveoppsett (Story 2.1):**

1. Lag en ny bruker og opprett et hjem (punkt 3 og 4 over). Du havner på **Sett opp oppgaver** med åtte anbefalte oppgaver, hver med **Ta med**, **Må**/**Bør** og **Hvor ofte**.
2. Gjør «Vask stekeovnen» til **Må** og velg **Hver 2. måned**, og fjern haken ved «Rens sluket». Trykk **Lagre oppgavene**. Du havner på oppgaveoversikten for hjemmet, som viser sju oppgaver med «Vask stekeovnen» blant Må-oppgavene og uten «Rens sluket». Tilbake-knappen i nettleseren tar deg ikke til skjemaet igjen.
3. Fjerner du alle hakene og trykker **Lagre oppgavene**, står det «Velg minst én oppgave.», og ingenting blir sendt.
4. Oppsettet kjøres én gang per hjem. Åpner du `/hjem/<id>/oppgaveoppsett` igjen etterpå, blir du sendt til oppgaveoversikten for hjemmet. Lagrer du i to faner, svarer serveren 409 på den andre, og den fanen går også dit.
5. Logg inn som Anders (leietaker). Han ser oppgavene Kari har satt opp for «Storgata 12», men kan ikke sette opp oppgaver selv; serveren svarer 403 på `POST /api/homes/{home_id}/tasks/setup` (prøv i <http://localhost:8000/docs> som i invitasjonseksempelet). En utleier som oppretter en ny utleiebolig, setter opp oppgavene med en gang, før noen leietaker er med; har et eldre hjem ingen oppgaver, står **Sett opp oppgaver** ved det under **Dine hjem** på **Innstillinger**.

**Prøv oppgaveoversikten (Story 2.2):** Steg 3 og 4 forutsetter en nyseedet database, siden de lager et nytt hjem.

1. Logg inn som Mari. `/` åpner oppgaveoversikten for hjemmet hennes. Alle **Må**-oppgaver står over alle **Bør**-oppgaver, også når en Bør-oppgave er forfalt. Mens seed-dataene er ferske, står «Rens sluket» (Må) med «Snart forfall» i gult og fet skrift, og «Støvsug og vask gulvene» (Bør) med «Forfalt — frist var …» i rødt. Antall dager («i dag», «i morgen», «om N dager») og hvilke oppgaver som er forfalt, flytter seg med datoen, siden oppgavene er satt opp relativt til dagen seed-en ble kjørt. «Snart forfall» betyr innen 3 dager, og det er serveren som avgjør det (`due_status` i `GET /api/homes/{home_id}/tasks`).
2. Trykk på en oppgave for å se detaljene. Der kan du endre **Må**/**Bør** og **Hvor ofte** (se Story 2.3 under). Trykk **Oppdater** øverst (eller dra lista ned på mobil) for å hente oppgavene på nytt; skjermleseren sier «Oppdatert». Bruk Tab: fokus går fra overskriften via **Medlemmer og invitasjon**, **Legg til oppgave** (for husstandsmedlemmer og utleiere, se Story 2.6 under) og **Oppdater** gjennom oppgavene ovenfra og ned (først avkrysningsboksen, så selve oppgaven, se Story 2.4 under), og til slutt fanelinja. **Husly** øverst er en lenke til `/`.
3. Logg inn som Kari, gå til **Innstillinger**, trykk **Opprett nytt hjem**, velg **Husstand** og sett opp oppgavene. Hun har nå to hjem, og oppgaveoversikten viser **Bytt hjem**.
4. Trykk **Bytt hjem** og velg «Storgata 12» under **Dine hjem**. Last siden på nytt og gå til `/` (eller trykk **Husly**): appen åpner «Storgata 12», fordi det er sist brukte hjem. Dette huskes i nettleseren (`localStorage`), per bruker og per enhet, ikke på serveren.

**Prøv å justere oppgaver (Story 2.3):** Forutsetter en nyseedet database, siden stegene endrer oppgavene.

1. Logg inn som Mari, trykk på «Rens sluket» og velg **Bør**. Ingenting lagres før du trykker **Lagre endringer**; da står det «Lagret». Trykker du uten å ha endret noe, står det «Ingen endringer å lagre.», og ingenting blir sendt.
2. Logg inn som Jonas i en annen nettleser (eller et privat vindu) og trykk **Oppdater** på oppgaveoversikten: «Rens sluket» står nå blant Bør-oppgavene.
3. Velg en ny verdi under **Hvor ofte** og lagre. Fristen flytter seg fra samme startpunkt: «Hver måned» → «Hver 2. måned» gir 30 dager senere frist. Velger du et kortere intervall, kan oppgaven bli forfalt med en gang. Endrer du bare Må/Bør, står fristen stille.
4. Logg inn som Anders (leietaker) og åpne en oppgave i «Storgata 12». **Viktighet** og **Hvor ofte** vises låst med «Satt av utleier», og kan nås med Tab, men ikke endres. Serveren svarer også 403 for ham, uansett innhold, hvis han prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `anders@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Hent id-en til «Storgata 12» med `GET /api/homes` og en oppgave-id med `GET /api/homes/{home_id}/tasks`.
   4. Kjør `PATCH /api/homes/{home_id}/tasks/{task_id}` med for eksempel `{"classification": "should"}`. Svaret er 403.
5. Går du fra siden uten å lagre, forkastes endringen uten advarsel.

**Prøv å krysse av oppgaver (Story 2.4):** Forutsetter en nyseedet database, siden stegene endrer oppgavene. Med Story 2.4 er også Story 2.5 (ny frist etter avkrysning) bygget.

1. Logg inn som Mari. «Avkalk vannkokeren» er allerede krysset av, med «Fullført … av Jonas» i grønt og overstreket navn: seed-en lar Jonas krysse den av to dager før seed-en ble kjørt.
2. Logg inn som Jonas i en annen nettleser (eller et privat vindu) og kryss av «Støvsug og vask gulvene». Boksen blir krysset av med en gang, uten bekreftelse, og kortet viser «Fullført i dag». Ditt eget navn står aldri der. Neste frist regnes fra dagen du krysset av (UTC) pluss hyppigheten, også når oppgaven var forfalt: «Hver 2. uke» gir frist om 14 dager. Også «i dag» og «i går» i notatet regnes i UTC-døgn, så en avkrysning like etter midnatt norsk tid kan stå som «Fullført i går».
3. Trykk **Oppdater** hos Mari: kortet viser «Fullført i dag av Jonas». Kortet står som fullført så lenge neste frist er mer enn 3 dager unna; når den nærmer seg, kommer fristen og en tom boks tilbake.
4. En avkrysset boks kan ikke angres. Den forblir krysset av, og et nytt trykk sender ingenting. Med Tab kommer du først til boksen («Merk «X» som fullført») og så til oppgaven.
5. Slå av nettet (i Chrome: DevTools → **Network** → **Offline**) og kryss av en oppgave hos Jonas. Kortet viser «Fullført i dag». Slå nettet på igjen: avkrysningen blir sendt av seg selv, uten at kortet hopper tilbake. **Begrensning:** avkrysninger som er gjort uten nett, ligger bare i minnet. Laster du siden på nytt eller lukker appen før nettet er tilbake, går de tapt, og du må krysse av på nytt.
6. Logg inn som Jonas, åpne **Medlemmer og invitasjon** og trykk **Forlat hjemmet**. Hos Mari står det nå «Fullført i dag av tidligere medlem»; avkrysningen blir stående.
7. Anders (leietaker) kan også krysse av oppgaver i «Storgata 12». Bildebevis kommer i Epic 4.

**Prøv å legge til og fjerne oppgaver (Story 2.6):** Forutsetter en nyseedet database, siden stegene endrer oppgavene.

1. Logg inn som Mari og trykk **Legg til oppgave** øverst på oppgaveoversikten. Lista viser katalogoppgavene hjemmet mangler, og **Egen oppgave** nederst. Ingenting er valgt på forhånd; trykker du **Legg til** uten å velge, står det «Velg en oppgave.».
2. Velg en katalogoppgave: anbefalt **Må**/**Bør** og **Hvor ofte** står ferdig valgt, og du kan endre dem. Lagre: oversikten viser «La til «X».» (leses opp av skjermleseren, vises bare én gang), og oppgaven står i lista med første frist i dag pluss hyppigheten.
3. Velg **Egen oppgave**: fokus går til navnefeltet. Navnet trimmes og må være 1–100 tegn. Et navn som en aktiv oppgave allerede har (også med andre store og små bokstaver, og også katalogoppgavenes navn), avvises med en melding ved feltet. Egne oppgaver kan aldri kreve bildebevis (Epic 4).
4. Åpne en oppgave og trykk **Fjern oppgaven**. Bekreftelsen kommer inline: «Oppgaven forsvinner fra lista for alle i hjemmet. Det som er gjort, blir stående.» Trykk **Ja, fjern oppgaven**: du kommer til oversikten med «Fjernet «X».», og oppgaven er borte for alle (trykk **Oppdater** hos Jonas). **Avbryt** sender ingenting. Oppgaven slettes ikke; den arkiveres, og det som er gjort, blir stående i databasen.
5. Legg til den samme katalogoppgaven igjen: den blir en ny oppgave med ny første frist. Fjerner du alle oppgavene, står det «Ingen oppgaver i hjemmet ennå.» med **Legg til oppgave**; oppsettet av oppgaver tilbys ikke på nytt.
6. Logg inn som Anders (leietaker): han ser verken **Legg til oppgave** eller **Fjern oppgaven**, og serveren svarer 403 på `POST /api/homes/{home_id}/tasks` og `DELETE /api/homes/{home_id}/tasks/{task_id}` (prøv i <http://localhost:8000/docs> som i Story 2.3). Før oppgavene er satt opp, svarer serveren 409 «Sett opp oppgavene først.» på en `POST`.

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

Testene trenger verken Docker, nettverk eller nøkler; de stopper enhver nettverkstilkobling som ikke går til maskinen selv, og sjekker at `.env.example` lister nøyaktig de variablene appen leser. De samme sjekkene kjører automatisk på hver PR og på `main` i GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)), sammen med seed-kommandoen (to ganger, med sjekk av at det blir nøyaktig fire brukere, to hjem, fire medlemskap, én invitasjonslenke og 16 oppgaver, og at ingen hjem blander roller: et husstandshjem har bare husstandsmedlemmer, en utleiebolig nøyaktig én utleier og ellers bare leietakere) og migreringene opp og ned mot Postgres 18, en sjekk av at den genererte API-klienten er oppdatert, og `npm run build`.

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

## Nettversjon (valgfri)

<https://g04husly.vercel.app> er en demo av den samme koden. Den trengs ikke for å kjøre, teste eller vurdere appen. Alt over fungerer uten den.

- **Oppsett:** Ett Vercel-prosjekt (`g04husly`) med `frontend/` og `backend/` som Vercel Services på samme domene ([`vercel.json`](vercel.json)). Alt under `/api` går til FastAPI, resten til React-appen. Databasen er Neon Postgres 18 i EU (Frankfurt), koblet til gjennom Vercels Neon-integrasjon, som setter `DATABASE_URL` og `DATABASE_URL_UNPOOLED`. `JWT_SECRET` (minst 32 byte) er satt for Production og Preview i prosjektinnstillingene; uten den starter ikke API-et på Vercel. React-appen får `index.html` for alle stier som ikke er filer, så lenker som `/logg-inn` fungerer direkte.
- **Oppdatering:** `main` publiseres automatisk. Hver PR får en egen forhåndsvisning med sin egen Neon-gren (`preview/<git-gren>`), som slettes når PR-en lukkes ([workflow](.github/workflows/neon-preview-cleanup.yml)).
- **Migreringer:** `alembic upgrade head` kjører i backendens byggesteg (`[tool.vercel.scripts]` i `backend/pyproject.toml`). En feilende migrering stopper bygget, så forrige versjon blir stående. En migrering som allerede er committet, blir likevel liggende i databasen selv om et senere byggesteg feiler, så migreringer må være bakoverkompatible med forrige versjon av koden.
- **Sjekk:** `/api/health` svarer at API-et lever, og `/api/health/db` at det når databasen.
- **Tilgang:** Bare prosjekteieren (Eirik) ser Vercel- og Neon-dashboardene. Ingen nøkler ligger i repoet; de står bare i Vercel- og GitHub-innstillingene.
- **Tilbakerulling:** Hvis Services-oppsettet må forlates, går vi tilbake til taggen `v0.1-for-vercel-hosting` (bare frontenden på Vercel): sett Root Directory til `frontend` og Framework Preset til **Vite** i prosjektinnstillingene.
