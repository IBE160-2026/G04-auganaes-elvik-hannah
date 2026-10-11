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

## Arbeidsform i gruppa

- **Språk:** snakk norsk med oss. BMAD-dokumentene (brief, PRD, UX, arkitektur, epics) skrives på engelsk, som konfigurert. Prosessdokumentasjon for sensor i `docs/` skrives på norsk.
- **Coaching path** i BMAD-skills. Vi vil bli tatt gjennom seksjon for seksjon og utfordret på tynne svar, ikke få et ferdig utkast fullt av antagelser.
- **Reviewer gates skal kjøres**, ikke hoppes over.
- **«Er det noe vi har glemt?»** betyr at du skal sjekke artefaktet på nytt mot kildene oppstrøms (brukerreiser UJ-1..4, åpne spørsmål i PRD, tidligere dokumenter). Det er ikke nok å gjenta at skillens sjekkliste passerte. Gjør gjerne denne sjekken uoppfordret.
- **Gjenoppta arbeid fra `.memlog.md`** i hver artefaktmappe. Den har hele beslutningshistorikken og går foran `review-*.md`-filene, som er øyeblikksbilder fra utkaststadiet.

## Mac og Windows

Gruppa jobber på både Mac (Eirik, Hannah) og Windows (Steffen, med Git Bash).

- Kjør `git pull` før du starter, og `git fetch` før push. Hvis noen andre har pushet, gjør du rebase. Aldri force-push.
- Linjeskift styres av `.gitattributes`. Hvis `git status` viser mange filer som endret uten at de er redigert, må det undersøkes før commit.
- To personer skal ikke redigere samme planleggingsdokument samtidig på hver sin maskin.
- Personlige BMAD-innstillinger ligger i `_bmad/custom/config.user.toml` (gitignored).
- Skript og kommandoer skal fungere i både zsh (Mac) og Git Bash (Windows). På Windows heter Python ofte `python` i stedet for `python3`.

## Status

Planleggingen (brief → PRD → UX → arkitektur → 6 epics / 23 stories) er ferdig, og faglærers tilbakemelding er fulgt opp med `bmad-correct-course` (se `_bmad-output/planning-artifacts/sprint-change-proposal-2026-10-11.md`). v1 er delt i Trinn 1 og Trinn 2, og appen skal kunne kjøres lokalt med Docker (FR-22, AD-15). Endringene er gjennomgått og slått sammen i PR #1. Sprint planning er gjort i PR #2, og rekkefølgen står i `_bmad-output/implementation-artifacts/sprint-status.yaml`. **Neste steg** er Story 1.1, deretter 1.2 og 1.6, med én GitHub-issue, branch og PR per story.

## KI-logg

Prompts fra Claude Code-økter eksporteres automatisk til `docs/ki-logg/okter/` av en Stop-hook (`.claude/settings.json` → `scripts/ki-logg/eksporter_okter.py`). Commit loggfilene sammen med arbeidet de hører til. Når en økt er ferdig, legger du til en linje om den i sammendragstabellen i [`docs/ki-logg/README.md`](docs/ki-logg/README.md).

## Faglærers tilbakemelding

Se `_bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/tilbakemelding-product-brief.md`. Hovedpunktene er å dele v1 i trinn 1 og trinn 2, lage testbare suksesskriterier og legge opp til lokal kjøring.
