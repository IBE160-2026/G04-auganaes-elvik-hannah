# Husly – IBE160 G04

Gruppeprosjekt i IBE160 Programmering med KI. Appen *Husly* planlegges med BMAD (`_bmad-output/planning-artifacts/`) og bygges med Claude Code.

## Vurdering styrer arbeidet

Alt arbeid vurderes etter sensorveiledningen i [`docs/sensorveiledning.md`](docs/sensorveiledning.md). Prosess og KI-styring teller mest (30 %). Sensor bedømmer både appen og *sporene av hvordan den ble laget*. Konsekvenser for hvordan du jobber:

- **Oppdater planen, ikke erstatt den.** Når krav endres, oppdaterer du brief, PRD, arkitektur og epics og skriver hvorfor (f.eks. med `bmad-correct-course`). Ikke generer dokumentene på nytt fra bunnen av.
- **Små, beskrivende commits.** Én commit per avgrenset endring, med norsk commit-melding som sier hva og hvorfor. Commit når en milepæl er nådd.
- **Én branch og én PR per story.** Branch-navn: `story/<epic>-<nr>-<kort-navn>`. PR-beskrivelsen lenker til storyen og beskriver hvordan endringen er testet og hva som ble rettet i KI-forslaget.
- **Sporbarhet.** Kode, tester og PR-er refererer til FR-/story-ID fra PRD og `epics.md`. Avvik fra planen forklares i PR eller i planleggingsdokumentet.
- **Kvalitetssikring.** Hver story skal ha automatiske tester av meningsfull logikk, f.eks. rolleregler og forfallsberegning. Feil som blir funnet i KI-generert kode, noteres i PR-en og i [`docs/ki-logg/korrigeringer.md`](docs/ki-logg/korrigeringer.md).
- **Kjørbar for sensor.** Appen skal kunne kjøres lokalt etter README, uten gruppens kontoer eller nøkler (lokal database, seed-data og mock-modus for KI og push). README og `.env.example` oppdateres i samme PR som endringen som krever det.
- **Rent repo.** Ingen hemmeligheter, `.env`, `node_modules`, `venv` eller byggeartefakter. Ingen død kode eller utkommenterte rester fra forkastede forsøk.

## KI-logg

Prompts fra Claude Code-økter eksporteres automatisk til `docs/ki-logg/okter/` av en Stop-hook (`.claude/settings.json` → `scripts/ki-logg/eksporter_okter.py`). Commit loggfilene sammen med arbeidet de hører til. Når en økt er ferdig, legger du til en linje om den i sammendragstabellen i [`docs/ki-logg/README.md`](docs/ki-logg/README.md).

## Faglærers tilbakemelding

Se `_bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/tilbakemelding-product-brief.md`. Hovedpunktene er å dele v1 i trinn 1 og trinn 2, lage testbare suksesskriterier og legge opp til lokal kjøring.
