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

### Åpne punkter
- B1: sjekk Cron Jobs-siden etter 07:00 norsk tid 23.11 (Invocations og status). Ikke deploy Production på nytt før da. B2 avventer.
- Issue #14 (Windows-testen): sjekk at den er lukket på GitHub, og noter resultatet.
- Skjermlesersjekken er droppet: de tre punktene i `deferred-work.md` (KI-popover, Story 3.4-bekreftelsen, porteføljens detaljkolonne) og de åpne Epic 2-, 4- og 6-punktene i `sprint-status.yaml` er ikke lukket. Før dem som godtatt kjent grense.
- PR #104: gjennomgå og merge.
- C2 (testdata i Neon) og Neon-sjekken står åpne.
- Cron Jobs i `vercel.json` er Legacy hos Vercel: vurder migrering til Schedules senere.
