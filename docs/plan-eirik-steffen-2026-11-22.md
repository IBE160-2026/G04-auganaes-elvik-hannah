# Plan for 22.11: Eirik og Steffen

Alle stories i planen er ferdige (Epic 1–6, med Story 1.10 «Slett konto» lagt til 21.11), og alle utsatte punkter er gjort bortsett fra push-påliteligheten (B2). Det som står igjen er å **se appen fungere** på ekte enheter og i nettleser, og å bestemme hva som skjer med B2. Rekkefølgen under er anbefalt: det som avgjør noe kommer først.

## Gjort 21.11 (Eirik og Claude)

- **Story 6.1, portefølje for utleier** (PR #87): fanen «Portefølje» med én rad per utleiehjem, status i tekst og to kolonner fra 600 px. FR-20 og AC rettet til «per hjem», siden modellen ikke har bygning.
- **Epic 5- og Epic 6-retrospektiv** skrevet, og Gemini-røyktest på Production: chat med historikk og velkomstguide svarer med ekte Gemini.
- **D1 og D2 fra Epic 5-retroen:** chatpolering (auto-scroll, makshøyde, mislykket melding blir stående, PR #88) og regelen om at KI-stories sier hva KI-en ikke skal gjøre (PR #89). A4 godtatt som kjent grense.
- **Story 1.10, slett konto** (FR-25, AD-17, `correct-course` i PR #91, bygget i PR #93): brukeren anonymiseres, avhengige rader og tomme hjem slettes med bilder, og en utleier med leietaker må fjerne leietakerne først.
- **Utsatt arbeid ryddet** (`deferred-work.md` har nå utfall per punkt, PR #90): fotorobusthet (avkuttet JPEG, gammelt bilde tilbake, PR #94), småfikser (e-post i små bokstaver i databasen, offline-melding, Bør-varsel, demo-markering, PR #95).
- **Postgres-samtidighetstester** for radlåsene (PR #96): 89 tester i CI, mutasjonssjekket (58 feilet uten låsene). De fant en feil i `invites.accept`, rettet.
- Alle PR-er har kjørt tre reviewere (eller én samlet for de små), og CI var grønn før merge. Migreringene er bekreftet kjørt mot Neon.

## 0. Oppstart (begge, i hver sin terminal)

Før dere begynner: `git pull`, og to personer skal ikke redigere samme planleggingsdokument samtidig.

```bash
git pull
docker compose up -d --wait            # lokal Postgres (Docker Desktop må kjøre)
cd backend && uv run python -m app.seed
uv run fastapi dev                      # backend på http://localhost:8000
```

```bash
cd frontend
nvm use                                 # Node 24 (vitest 5.0.5 henger på Node 26.7, se README)
npm install && npm run dev              # http://localhost:5173
```

Windows (Steffen, Git Bash): Python heter ofte `python`, og `.gitattributes` styrer linjeskift. Viser `git status` mange endrede filer uten at dere har rørt dem, så undersøk før commit.

Eksempelbrukere (passord `husly-demo`): Mari, Jonas (husstand), Kari (utleier), Anders (leietaker). E-postene står i README.

## 1. B1: ekte push og første cron-kjøring (Eirik, med en enhet)

Dette avgjør om B2 skal bygges eller kuttes, så det tas først.

1. Åpne <https://g04husly.vercel.app> på en telefon eller et skrivebord der nettleseren støtter push (Safari på iPhone krever at appen legges på hjemskjermen først). Logg inn, gå til **Innstillinger → Slå på varsler** og tillat varsler. Enheter som ble slått på med utviklingsnøkkelen må slå på igjen.
2. Logg inn som utleier på en annen enhet eller et annet vindu, åpne **Administrer hjemmet**, send en melding under «Send melding til leietakerne», og se at den kommer fram på enheten (leietakeren må være i utleierens hjem).
3. Vercel → `g04husly` → Settings → **Cron Jobs**: se om kjøringen 06:00 UTC gikk i dag (Hobby-planen beholder bare ca. en times logger, så dashboardet er eneste sted).
4. **Beslutning:** virker push, er B2 «nice to have»: dere kan kutte den eller bygge de to viktigste (401/403 fra gamle enheter og tidsbudsjett per medlem). Virker den ikke, rett feilen først. Resultatet føres i `action_items` i `_bmad-output/implementation-artifacts/sprint-status.yaml` (B1 og B2).

## 2. Windows-testen, issue #14 (Steffen)

Følg README fra «Kom i gang» i Git Bash. Skriv funn i issue #14, og lag én issue, branch og PR per rettelse (`story/<epic>-<nr>-<navn>` eller `fix/<navn>`).

- Kjør `uv run pytest` og `npm test -- --run`.
- Prøv oppskriftene «Prøv porteføljen», «Prøv å slette konto» og «Prøv å legge til og fjerne oppgaver» i README.
- Valgfritt hvis Docker kjører: Postgres-testene med `HUSLY_POSTGRES_TEST_URL=postgresql+psycopg://husly:husly@localhost:5433/postgres uv run pytest tests/postgres -v`. De er bare kjørt i CI hittil.

## 3. Se det som ikke er sett i nettleser (begge)

- **Portefølje:** logg inn som Kari, opprett et andre utleiehjem (Innstillinger → Opprett nytt hjem → Utleiebolig, sett opp oppgaver) og åpne **Portefølje**. Sjekk 320, 700 og 1200 px: én kolonne under 600 px (raden er en lenke), to kolonner over, og at headeren ser riktig ut ved siden av den utvidede kolonnen (`.app-shell__main:has(.portfolio)` i `frontend/src/routes/Portfolio.css`).
- **Slett konto:** README «Prøv å slette konto». Se at utleier med leietaker får beskjed om å fjerne leietakerne først, og at Jonas sin historikk står igjen som «Tidligere medlem» hos Mari.
- **Chatten (D1):** åpne «Spør KI» på en oppgave → «Spør mer» og send fire–fem meldinger. Feltet skal bli stående i bildet, og en mislykket melding (slå av nettet) skal bli stående med «Prøv igjen».
- **Offline-melding:** slå av nettet i «Administrer hjemmet» og prøv å sende en melding: «Vi fikk ikke kontakt med tjenesten…» med «Prøv igjen».

## 4. Skjermlesersjekk, C1 (begge, deler på to)

Én runde med VoiceOver (Mac, `Cmd+F5`) eller NVDA (Windows) over:
bildeopplasting (`PhotoUpload`), bildevisning (`PhotoEvidenceView`), KI-popoveren, chatten og porteføljens detaljkolonne. Kjente spørsmål (`_bmad-output/implementation-artifacts/deferred-work.md`): kunngjøres det at detaljkolonnen bytter når en rad velges, og leses «Oppdatert» opp etter «Oppdater»? Funn føres som issues eller i `deferred-work.md`; lukk Epic 2-, 4- og 6-punktene i `sprint-status.yaml` sammen når runden er gjort.

## 5. Opprydding (Eirik)

- **Testdata i Neon (C2):** testbrukeren `rooktest-…@example.com` og hjemmet «Røyktest 6.1 …» ligger i Production. Slett i Neon-konsollet, eller si fra til sensor. Brukeren har et tilfeldig passord som ikke ble lagret, så **Slett konto** er ikke et alternativ; slett raden i Neon-konsollet.
- **Neon-konsollet:** sjekk at gamle preview-branches fra PR #11–#22 er borte (tiltak 5).
- **Vercel:** slett gamle preview-deployments (75 % funksjonslagring brukt).

## 6. Til slutt (begge)

- Spørsmålet om nudgen (FR-11) **erstatter** eller **kommer i tillegg** til den vanlige påminnelsen: PRD og kode sier «erstatter». Bekreft, så lukkes punktet.
- Ferdig for sensor? Kjør README fra en nyklonet mappe (uten egne kontoer eller nøkler) på begge maskinene, og sjekk at `docs/ki-logg/` og `.logs/` er committet.
- Legg en linje om økten i `docs/ki-logg/README.md`, og bruk `sesjonslogg` før dere avslutter.

## Status nå (21.11)

| Område | Status |
|---|---|
| Stories 1.1–6.1 og 1.10 | ferdige og merget |
| Retrospektiver Epic 1–6 | gjort |
| Utsatt arbeid (`deferred-work.md`) | gjort, bortsett fra B2 |
| Postgres-samtidighetstester | i CI (89 tester, mutasjonssjekket) |
| Migreringer mot Neon | bekreftet kjørt (`deleted_at`, e-post-CHECK) |
| **Åpent** | B1, B2, C1, C2, Windows-testen, nettlesersjekk |

Se også: `.logs/eirik/issues.md` (åpne punkter) og `_bmad-output/implementation-artifacts/epic-6-retro-2026-11-21.md`.
