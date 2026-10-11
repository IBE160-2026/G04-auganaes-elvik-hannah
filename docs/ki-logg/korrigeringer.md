# Eksempler på styring og korrigering av KI

Utvalgte situasjoner der vi ikke bare godtok det KI foreslo. Hvert eksempel lenker til prompten i KI-loggen og til stedet i repoet der endringen havnet. Listen oppdateres fortløpende. Fra implementeringen av starter, kommer eksempler fra PR-er og kodegjennomgang i tillegg.

Forkortelser: **B44** = [økt 12.09–04.10](okter/2026-09-12_eirik_44c18c13.md), **A29** = [arkitekturøkt 04.10](okter/2026-10-04_eirik_29c07691.md), **E19** = [epics-økt 04.10](okter/2026-10-04_eirik_192ee825.md), **S11** = [Steffens correct course-økt 11.10](okter/2026-10-11_steffen-elvik_f2e2dde9.md). Tallet etter `#` er nummeret på innlegget i loggfila.

## Presiserte krav (KI måtte endre forslaget sitt)

| # | Situasjon | Vår korrigering | Hvor det havnet |
|---|---|---|---|
| 1 | Det var uavklart om utleier kunne bo sammen med leietakerne. | «Vi trenger ikke ta høyde for at utleier kan bo med leietakere.» Dette forenklet rollemodellen. (B44 #45) | PRD, rollemodell (FR-3) |
| 2 | Uklart hvordan neste forfallsdato beregnes når en oppgave gjøres for sent. | Vi fastsatte regelen: full frekvens regnes fra faktisk utført dato, slik at to dagers forsinkelse fortsatt gir 30 nye dager. (B44 #49) | `prd.md` FR om omplanlegging. Testbar regel for senere. |
| 3 | Det var uavklart hva bildebevis kunne brukes til, og hvem som kunne se bildene. | Bildebevis skal bare brukes der det er lett å se at oppgaven er gjort (f.eks. sluk). Bildet erstattes ved neste utførelse og vises bare til utleier og support. (B44 #40, #53) | PRD FR-18/19. Arkitekturen håndhever en systemkuratert liste på serversiden. |
| 4 | KI påpekte risikoen ved at assistenten gir råd om kjemikalier. | Vi ville beholde generelle råd, men med en tydelig ansvarsfraskrivelse om at KI kan ta feil og at man skal være forsiktig med kjemikalier. (B44 #56) | `prd.md` FR-14/15, krav om disclaimer |
| 5 | KI foreslo fargepaletter. | Vi avviste de første forslagene: «Vi trenger litt lysere farger, samt rosa og lyselilla.» Vi valgte deretter alternativ 1 med krav om at farger skal kunne justeres. (B44 #63–67) | `DESIGN.md`, fargetokens |
| 6 | KI spurte om frontend-rammeverk og tolket svaret «java» bokstavelig. | Vi presiserte at det gjaldt JavaScript, ba om en anbefaling og valgte React selv. (A29 #2–9) | `75186a6`, `EXPERIENCE.md` breakpoints |
| 7 | KI la fram alternativer for AI-leverandør. | Vi krevde en gratis løsning og spurte om vi kan bytte senere hvis gratisvarianten ikke holder. (A29 #18, #23) | `ARCHITECTURE-SPINE.md`, AI-gateway (Gemini Flash-Lite bak ett grensesnitt) |
| 8 | KI spurte om brief skulle brukes som input til epics. | Vi ba om fordeler og ulemper og bestemte at brief holdes utenfor, fordi PRD allerede dekker den og brief nevner v2-ting. (A29 #30–31, E19 #2) | `epics.md`, kildeliste |
| 9 | KI foreslo SQLite som lokal database for sensor. | Vi spurte om det ikke var mer naturlig med Docker, som faget har lært oss for å jobbe på tvers av maskiner. Vi valgte Postgres i Docker, slik at databasen blir den samme lokalt som i drift. (S11 #9) | `ARCHITECTURE-SPINE.md` AD-15, PRD FR-22 |
| 10 | KI foreslo hvordan KI-funksjonen skulle deles mellom trinn 1 og trinn 2. | Vi spurte hvor krevende hurtigsvar og chat er, og hva sensor trenger for at det skal virke, før vi godtok bare hurtigsvar i trinn 1 med mock-modus uten nøkkel. (S11 #11–12) | PRD §6 og FR-14, epics Story 5.1 |

## Kvalitetssikring av KI-generert innhold (reviews)

Vi har bedt KI om uavhengige gjennomganger av sitt eget arbeid før dokumentene ble ferdigstilt, og vi har tatt stilling til funnene.

| Dokument | Review | Funn | Utfall |
|---|---|---|---|
| PRD | [`review-rubric.md`](../../_bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/review-rubric.md) | Rollen «Owner» var ikke avstemt med de tre rollene. KI-assistenten manglet sikkerhetskrav. Risikoen ved stort omfang var ikke håndtert med en prioritert kuttrekkefølge. | «Owner» ble fjernet fra rollemodellen, krav om disclaimer ble lagt til, og en foreløpig kuttrekkefølge ble lagt inn (`prd.md` OQ-1). Faglærer påpekte senere den samme omfangsrisikoen, og den følges nå opp med trinn 1/2. |
| UX | [`review-accessibility.md`](../../_bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/review-accessibility.md) | 15 funn (1 kritisk, 4 høye). Blant annet ga success-fargen #2F9E6E kontrast 3,37:1 og warning-fargen #D98A2B 2,76:1, under WCAG AA-kravet på 4,5:1. Zoom og reflow manglet. | Fargene ble mørknet til #267F59 og #9E641F (≥ 4,5:1), se `DESIGN.md`. |
| Arkitektur | [`review-adversarial.md`](../../_bmad-output/planning-artifacts/architecture/architecture-prosjektoppgave-ibe160-2026-10-04/reviews/review-adversarial.md) + rubric og versjonssjekk | 2 kritiske og 5 høye funn. Eksempel: bildebevis ble lagret per `Task`, mens datamodellen var per `TaskInstance`. Da ville utleier sett feil bilde etter andre utførelse. | `PhotoEvidence` gjort 1:1 med `Task` med peker til siste instans, se `ARCHITECTURE-SPINE.md`. |

## Feil i KI-output som vi fant og rettet

| Feil | Hvordan den ble oppdaget | Retting |
|---|---|---|
| YAML-frontmatter i brief knakk på grunn av kolon i tittelen («mapping values are not allowed»). | GitHub viste feilmelding, og vi spurte KI hva den betydde (B44 #28). | `215dc33` |
| KI fant ikke frontend-valget og antok at det var tatt. | Vi spurte «Klarer du å finne de?» (A29 #2). Det viste seg at valget aldri var tatt. | Låst i `75186a6` |
| Eksporten av KI-loggen (`eksporter_okter.py`) tok med hele skriptfilen som «Avviste KI-forslag». Sjekken lette etter avslagsteksten hvor som helst i et verktøyresultat, og skriptet inneholder selv den teksten. | Vi testet autolagringen og leste den genererte loggfila (økt 11.10, 13:05). | Sjekken krever nå at resultatet *begynner* med avslagsteksten (PR #1, `scripts/ki-logg/eksporter_okter.py`). |
| AD-13 i arkitekturen brukte primærfargen `#7B6EE3`, mens DESIGN.md og epics bruker `#6E62CC`. | Kryssjekk av dokumentene under correct course (S11). | `772755c` |
| Dokumentene sa 20 stories, men det fantes 22, og nå 23. | Kryssjekk under correct course (S11). | `77ed396`, `41170f2` |
| Etter at suksesskriteriene fikk nye nummer, pekte motvektene SM-C1/C2 fortsatt på de gamle numrene. | Kryssjekk under correct course (S11). | `29615bf` |
| Da det gamle samlekriteriet SM-1 ble erstattet, mistet FR-1 (opprette hjem), FR-4 (anbefalt Must/Should) og FR-21 (responsivt) sporingen til et suksesskriterium. «FR-1 through FR-21» sto igjen i arkitektur og epics etter at FR-22 kom til, og briefen sa JavaScript mens arkitekturen har TypeScript. | Eirik gjennomgikk PR #1 fra Mac før merge. | Brief kriterium 3 og 5, PRD SM-3 og SM-5, arkitektur `scope`, `epics.md` (PR #1) |

## Ekstern tilbakemelding

Faglærers tilbakemelding på brief (06.10) pekte på stort omfang, utestbare suksesskriterier og at sensor ikke kan kjøre appen lokalt. Se [`tilbakemelding-product-brief.md`](../../_bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/tilbakemelding-product-brief.md). Hvordan vi følger dette opp, dokumenteres i oppdateringene av brief, PRD, arkitektur og epics.
