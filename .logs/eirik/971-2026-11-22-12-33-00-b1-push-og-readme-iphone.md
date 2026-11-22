# B1: ekte push, cron-sjekk og README om iPhone-varsler

## 2026-11-22 kl. 12:33 — Eirik

### Oppgave
Fortsette etter nettlesersjekken: bekrefte ekte push og første cron-kjøring (B1), og finne ut hvorfor Steffens iPhone sa «Varsler støttes ikke her». Eirik avgjorde underveis at skjermlesersjekken (C1/A3) ikke er nødvendig, og at Steffen har gjort Windows-testen.

### Plan
- Sjekke Vercel (CLI og dashbord) for cron og miljøvariabler.
- Finne årsaken til push-meldingen på iPhone i `frontend/src/api/push.ts`.
- Legge forklaringen i README (liten egen branch og PR).
- Klargjøre lokalt miljø for skjermlesersjekken, men dette ble droppet.

### Resultat
- **Cron:** Production har `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` og `CRON_SECRET`. På Settings → Schedules → Cron Jobs (Legacy-visning) er `/api/internal/run-due-check` Active, 06:00 UTC, men Invocations og P75 viste «—». Hobby-planen beholder ikke runtime-logger lenger enn ca. 30 min, så `vercel logs` kunne ikke svare. Første kjøring er derfor **ikke bekreftet**. Dashbordet merker Cron Jobs som deprecated til fordel for Schedules.
- **Push til iPhone:** Meldingen skyldtes at Steffen åpnet Husly i Safari. Fra Hjem-skjerm-ikonet virker det. Eirik bekreftet at en utleiermelding (Story 3.4) kom fram på Steffens iPhone mot Production. Mistanken om en race i `readPushStatus` var feil, så ingen koderettelse.
- **README:** én linje om at iPhone-varsler krever åpning fra Hjem-skjerm-ikonet (`1d06201`, branch `docs/readme-iphone-varsler`, PR #104). PR-en inneholder også de tidligere upushede `6f95940` (sjekkliste for skjermlesersjekk) og `6d66720` (KI-loggeksport).
- **Kunnskap:** Minste hyppighet er 7 dager, så en ny oppgave kan ikke få frist i morgen via appen. En frist må i så fall flyttes direkte i Neon (`task_instances.due_on`), og jeg gjorde ikke det. Cron-kallet registreres uavhengig av om noen får push.
- **Lokalt:** `uv run python -m app.seed` ble kjørt (gjenskapte Kari og Jonas, 8 oppgaver i Storgata 12). Kun lokal database.
- **Avgjort av Eirik:** skjermlesersjekken (C1) er ikke nødvendig. Windows-testen (issue #14) er gjort av Steffen.
- **PR #104 merget** (merge-commit `1ce852f`, alle sjekker grønne, også Windows). Merge-en utløste en ny Production-deploy (`g04husly-axce76l6x`) via Git-integrasjonen. Det påvirker ikke abonnementer (de ligger i Neon, VAPID-nøklene er uendret) og cron (`vercel.json` uendret), men jeg burde ha sagt fra før merge siden jeg hadde bedt om ingen deploy før cron-testen.
- **Steffens Windows-test (issue #14, lukket 22.11)**, lest fra GitHub: `uv run pytest` 1046 bestått og 88 Postgres-tester bestått mot Docker; vitest 603 av 603 bestått; prøvd etter README (portefølje ved 320/700/1280 px, slett konto, legge til og fjerne oppgave) uten avvik fra README; Anders (leietaker) fikk 403 på å legge til og fjerne oppgaver (testet mot API-et, ikke skjulte knapper i grensesnittet). Funn 1: seed-utskriften viste «�» for æøå på Windows, rettet i **PR #105** (`fix/seed-utf8-utskrift`, åpen, CI grønn). Funn 3 (innrykk i detaljkolonnen) er løst av PR #100. Funn 2: vitest hang ikke på Node 26.7 hos Steffen, selv om README og `CLAUDE.md` sier at 5.0.5 gjør det på Eiriks Mac.
- **Gjennomgang mot sensorveiledningen og lærerens tilbakemeldinger** (Claude, uten å kjøre tester eller følge README på ren maskin): prosess og KI-styring sterk (465 commits, 74 PR-er, 31 issues, 35 KI-økter, 148 rader i `korrigeringer.md`); briefens og PRD-ens tilbakemeldinger er fulgt opp (Trinn 1/2, kuttlinje, lenkeregler, KI-feil, glossar, FR-count, SM-9 delt). Svakheter: README manglet «hva er Husly», skjermlesersjekken droppet, B1 ikke bekreftet, commit-fordeling (Hannah har avsluttet studiet; Eirik og Steffen programmerte sammen fra Eiriks maskin), `docs/sensorveiledning.md` sier «tester (kommer)», CLAUDE.md-status er ca. 25 KB.
- **README-endring (punkt 1 fra gjennomgangen):** ny seksjon «Hva er Husly», overskrift «Husly – IBE160 G04» (var «G04 — EHS»), mock-avsnittene delt i punkter uten å endre ordlyd, og en note om Hannah og felles maskin. Committet som `719ed43` på grenen `docs/readme-hva-er-husly` (basert på `origin/main`), **ikke pushet**.
- **Lokalt:** `main` er i synk med `origin/main` etter at grenen ble slettet. Steffen har ikke lastet opp bilder; Blob-lagringen kunne ikke listes uten token (ikke hentet uten Eiriks ja).

### Åpne punkter
- B1: sjekk Cron Jobs-siden etter 07:00 norsk tid 23.11 (Invocations og status). Ikke deploy Production på nytt før da. B2 avventer.
- PR #105 (seed-utskrift, Steffen) er åpen: merge etter cron-testen 23.11, siden en merge til `main` bygger Production på nytt.
- Node 26.7 og vitest: Steffen kjørte 603 tester uten hang. Avklar om README og `CLAUDE.md` bør justeres (maskinavhengig?).
- Skjermlesersjekken er droppet: de tre punktene i `deferred-work.md` (KI-popover, Story 3.4-bekreftelsen, porteføljens detaljkolonne) og de åpne Epic 2-, 4- og 6-punktene i `sprint-status.yaml` er ikke lukket. Før dem som godtatt kjent grense.
- Push `docs/readme-hva-er-husly`, åpne PR og merge etter cron-sjekken 23.11 (sammen med PR #105): README-endringen er committet lokalt, ikke pushet. Sjekk formuleringen om Hannah i «Medlemmer».
- Resten av gjennomgangen: lukk de åpne skjermlesersjekk-punktene som kjent grense, rett «tester (kommer)» i `docs/sensorveiledning.md`, kort ned statusen i `CLAUDE.md`, vurder en `.mailmap` og en tørrkjøring av README fra en ren klon.
- C2 (testdata i Neon) og Neon-sjekken står åpne.
- Cron Jobs i `vercel.json` er Legacy hos Vercel: vurder migrering til Schedules senere.
