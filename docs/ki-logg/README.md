# KI-logg

Her ligger sporene etter hvordan gruppen har brukt og styrt KI i prosjektet.

| Fil | Innhold |
|---|---|
| [`okter/`](okter/) | Én fil per Claude Code-økt. Inneholder alle prompts ordrett, svarene våre på spørsmål fra KI, avviste forslag, og hvilke commits økta førte til. |
| [`korrigeringer.md`](korrigeringer.md) | Utvalgte eksempler på at vi har presisert krav, avvist eller rettet KI-forslag, og hvor det endte i repoet. |

## Slik lages loggen

Claude Code lagrer hver økt lokalt som en transkripsjon. Skriptet [`scripts/ki-logg/eksporter_okter.py`](../../scripts/ki-logg/eksporter_okter.py) gjør transkripsjonen om til Markdown:

- **Automatisk:** en Stop-hook i [`.claude/settings.json`](../../.claude/settings.json) kjører skriptet etter hvert svar fra Claude. Da holdes loggen for økta oppdatert mens vi jobber.
- **Manuelt:** `python3 scripts/ki-logg/eksporter_okter.py` eksporterer alle økter på maskinen din for dette repoet. På Windows heter kommandoen `python` i stedet for `python3`. Hvert gruppemedlem kjører dette én gang for å få med økter fra før hooken ble lagt inn.

Krav: Python 3.8 eller nyere. På Windows må også Git for Windows (Git Bash) være installert, fordi Claude Code kjører hooken der. Hooken prøver først `python3` og deretter `python`.

Filene får navn etter dato, git-brukernavn og økt-ID, så økter fra ulike maskiner kommer ikke i konflikt. Skriptet fjerner personlige stier, e-postadresser og alt som ligner API-nøkler. Les likevel gjennom filene før de committes.

KI-ens egne svar er ikke med, fordi de er for omfattende. Resultatet av dem ligger i planleggingsdokumentene og commitene som hver økt lenker til.

## Oversikt over øktene

| Dato | Hvem | Fase | Hva skjedde | Resultat |
|---|---|---|---|---|
| 07.09 | Eirik | Oppstart og idé | Installerte og testet BMAD. Brainstormet med fasilitator-agenten fra faglærers liste over prosjektforslag. Kom fram til kjerneproblemet: uregelmessige husoppgaver «uten fast rytme» glemmes. | [økt](okter/2026-09-07_eirik_61ef1f62.md) · brainstorming i `_bmad-output/brainstorming/` |
| 12.09 | Eirik | Product brief | Coaching-modus. Vi beskrev problemet, fire brukersegmenter, må/bør-oppgaver, utleierroller og KI-hjelper. Betaling og Hybel-integrasjon ble satt utenfor v1. Kontrollerte at KI fulgte BMAD-prosessen, satte opp git og rettet en YAML-feil. | [økt](okter/2026-09-12_eirik_44c18c13.md) · `42dffb2`, `215dc33` |
| 29.09 | Eirik | PRD og UX | Journey-ledet PRD med personaene Mari/Peter, Johan og Martin. Vi presiserte forfallsregel, personvern for bildebevis og ansvarsfraskrivelse for KI-svar om kjemikalier. Valgte visuell retning («Sbanken, ikke DNB») og ba om lysere farger. Tilgjengelighetsreview fant kontrastfeil, som ble rettet. | samme økt · `2f5ad58`, `61d96dc`, `e75a98e` |
| 04.10 | Eirik, Hannah, Steffen | Arkitektur | Gjennomgang av status. Låste React og TypeScript, FastAPI, SQLModel, Gemini Flash-Lite (krav om gratis), PWA og hosting. Adversarial review fant 2 kritiske og 5 høye funn, som alle ble rettet. | [økt](okter/2026-10-04_eirik_29c07691.md) · `75186a6`, `60ba8b6` |
| 04.10 | Eirik | Epics og stories | Godkjente struktur med 6 epics og 20 stories. Holdt brief utenfor som input (bevisst valg) og kjørte en ekstra sjekk av dekningen. | [økt](okter/2026-10-04_eirik_192ee825.md) · `70703c3` |
| 08.10 | Eirik | Pause | Faglærers tilbakemelding på brief var mottatt. Bestemte at vi venter med videre arbeid til gruppen har gått gjennom den sammen. | samme økt |
| 10.10 | Eirik | Prosessoppsett | Mottok sensorveiledningen. Satte opp KI-logg, `CLAUDE.md` og sammendraget av sensorveiledningen, slik at videre arbeid følger kriteriene. | [økt](okter/2026-10-10_eirik_a0c373c0.md) |

Korte økter uten innhold, for eksempel en økt som ble avsluttet straks for å starte på nytt, ligger i `okter/`, men er ikke med i tabellen.
