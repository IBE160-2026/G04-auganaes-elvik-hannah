# Refleksjon: hva tok vi fra koden tilbake til kravene?

Svar på refleksjonsspørsmål 2 i faglærer Bård Pettersens PRD-tilbakemelding av 12.11 ([`tilbakemelding-prd.md`](../../_bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/tilbakemelding-prd.md)):

> Dere har endret PRD-en flere ganger etter at KI-assistert utvikling har pågått. Hva tok dere med fra koden og tilbake til kravene, og hvordan sjekket dere at kravteksten fortsatt stemmer med det som er bygget?

Hver endring nedenfor har en datert `sprint-change-proposal` eller en rad i [`korrigeringer.md`](korrigeringer.md). Spørsmål 1 (hvem avgjør hva «rettferdig» betyr i FR-11) er ikke besvart her.

## Hva som gikk fra kode til krav

| Funn under bygging | Hva kravene fikk | Hvor det står |
|---|---|---|
| Story 1.3: et utleiehjem finnes før første leietaker er med. | FR-3 sier «zero or more Tenants». | Epic 1-retro (S4), `sprint-change-proposal-2026-11-08.md` |
| Story 1.8 og retroen: ingen vei ut av et hjem, og historikk må overleve at et medlem forlater. | Nytt FR-23 og AD-16 («Tidligere medlem»). | `sprint-change-proposal-2026-11-08.md` |
| Story 2.1: faste intervaller i stedet for et fritt tall, og oppsettet kjøres én gang per hjem. | Intervallene og oppsettsregelen står i FR-8. | `sprint-change-proposal-2026-11-09.md` |
| Issue #30 og #31 under 2.1: utleiere kunne ikke lage eget husstandshjem, og oppgaver kunne ikke legges til eller fjernes. | Én regel for å opprette hjem (FR-1) og nytt FR-24. | `sprint-change-proposal-2026-11-09.md` |
| I dag: arkitekturen (AD-9) hadde allerede «ingen av de 3 siste», og appen har ingen «unit type». | FR-11-terskelen, og FR-16 uten «unit type». | `sprint-change-proposal-2026-11-12.md` |

## Hvordan vi sjekket at kravteksten stemmer med det som er bygget

- **Én prosess for endringer.** Hver endring i krav går via `bmad-correct-course` og gir en datert proposal. PRD-en blir oppdatert, ikke generert på nytt.
- **Tester som peker på kravene.** Tester og PR-er refererer til FR-/SM-ID. To regler sjekkes automatisk i CI: FR-3 (`domain/homes.fr3_violations`) og at hver rute med `{home_id}` har `require_role` (`tests/test_permissions.py`).
- **Å lese kravene mot koden, ikke mot minnet.** I dag sjekket vi Bårds tilbakemelding mot koden før vi svarte. Det avdekket at «unit type» ikke finnes (`task_types.py`, `HomeOut`), at e-post aldri sendes til andre medlemmer (`MemberOut`), og at `photo_evidence_eligible` allerede var avgjort i katalogen.
- **Reviewere som leser kravene.** Blind Hunter fant i Story 2.1 at PRD-en ikke hadde fått de faste intervallene. Funnet står i `korrigeringer.md`.
- **«Er det noe vi har glemt?»** kjøres mot brukerreisene UJ-1 til UJ-4 og de åpne spørsmålene i PRD-en, ikke bare mot skillens sjekkliste.

## Det som ikke var bra nok

- Endringene fra Story 2.1 kom inn i PRD-en først etter at en reviewer pekte på det. Prosessen fanget det, men sent.
- Vi la historikk og kode inn i selve kravene (`[REVISED …]`, funksjonsnavn, HTTP-koder). Da kan kravteksten og koden komme ut av takt, slik Bård skriver i 4.4. Kravene er nå skrevet rene, og historikken ligger i en Revision log med lenker.
- KI-en skrev FR-16 mot en «unit type» som ikke finnes. Menneskene leste ikke dette mot koden før Bård pekte på det, og det står nå i `korrigeringer.md`.

## Forslag til neste steg (ikke gjort ennå)

Be reviewerne i `bmad-build` sjekke om en endret regel også står i PRD-en og `epics.md`, ved å legge det til i `_bmad/custom/review-conventions.md`. Det flytter sjekken fra «når noen legger merke til det» til hver story.
