# Påminnelse: Eirik og Steffen jobber sammen 22.11

Alle stories i planen er ferdige (Story 6.1 merget i PR #87). Dette gjenstår, i rekkefølgen vi anbefaler.

1. **B1: ekte push og første cron-kjøring (Eirik, Vercel-innlogging).**
   - Slå på **Varsler** under Innstillinger på en enhet i Production (https://g04husly.vercel.app). Enheter som ble slått på med utviklingsnøkkelen må slå på igjen.
   - Logg inn som utleier, send en melding under **Administrer hjemmet**, og sjekk at den kommer fram på enheten.
   - Åpne Vercel → `g04husly` → Settings → **Cron Jobs** og se om kjøringen 06:00 UTC gikk (Hobby-planen beholder bare ca. 1 times logger, så loggen må leses i dashboardet).
   - Er det ok, kan B2 (push-pålitelighet) avgjøres; ellers avgjør vi hva som kuttes. Se `action_items` i `_bmad-output/implementation-artifacts/sprint-status.yaml`.
2. **Windows-testen, issue #14 (Steffen, Git Bash).**
   - `git pull`, så følg README fra «Kom i gang»: Docker, `uv run python -m app.seed`, backend og frontend. På Windows heter Python ofte `python`.
   - Prøv særlig **Prøv porteføljen (Story 6.1)** og **Prøv å legge til og fjerne oppgaver**, siden de er nyest. Skriv funn i issue #14 og lag én issue, branch og PR per rettelse.
   - Frontend-testene kjøres på Node 24 (se README), og `.gitattributes` styrer linjeskift: er mange filer endret uten at dere har rørt dem, undersøk før commit.
3. **Skjermlesersjekk, C1 (begge, VoiceOver på Mac eller NVDA på Windows).**
   - Én runde over bildeopplasting (`PhotoUpload`), bildevisning (`PhotoEvidenceView`), KI-popoveren og porteføljens detaljkolonne.
   - Se `_bmad-output/implementation-artifacts/deferred-work.md`: ingen kunngjøring når detaljkolonnen bytter, og live-region i skjult panel i KI-popoveren. Lukk Epic 2-, 4- og 6-punktene i `sprint-status.yaml` sammen.
4. **Porteføljens layout i nettleser (Eirik eller Steffen).**
   - Logg inn som Kari, opprett et andre utleiehjem, åpne **Portefølje** og sjekk ved 320, 700 og 1200 px.
   - Se særlig at headeren ser riktig ut ved siden av den utvidede kolonnen (`.app-shell__main:has(.portfolio)` i `frontend/src/routes/Portfolio.css`).
5. **Testdata fra røyktesten (Eirik).**
   - Testbrukeren `rooktest-…@example.com` og hjemmet «Røyktest 6.1 …» ligger i den delte Neon-databasen (Production). Det finnes ingen slette-rute: slett i Neon-konsollet, eller si fra til sensor.
   - Sjekk samtidig Neon-konsollet for gamle preview-branches (tiltak 5, PR #11–#22).

Se også: `.logs/eirik/issues.md` og `_bmad-output/implementation-artifacts/epic-6-retro-2026-11-21.md`.
