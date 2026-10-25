# Eksempler på styring og korrigering av KI

Utvalgte situasjoner der vi ikke bare godtok det KI foreslo. Hvert eksempel lenker til prompten i KI-loggen og til stedet i repoet der endringen havnet. Listen oppdateres fortløpende. Fra implementeringen av starter, kommer eksempler fra PR-er og kodegjennomgang i tillegg.

Forkortelser: **B44** = [økt 12.09–04.10](okter/2026-09-12_eirik_44c18c13.md), **A29** = [arkitekturøkt 04.10](okter/2026-10-04_eirik_29c07691.md), **E19** = [epics-økt 04.10](okter/2026-10-04_eirik_192ee825.md), **S11** = [Steffens correct course-økt 11.10](okter/2026-10-11_steffen-elvik_f2e2dde9.md), **K25** = [Story 1.1-økt 25.10](okter/2026-10-25_eirik_4408f289.md). Tallet etter `#` er nummeret på innlegget i loggfila.

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
| 11 | KI foreslo å skrive den anbefalte oppgavelista rett inn i Story 2.1. | Vi gjorde den til en versjonert `TaskType`-katalog i repoet, slik at bildebevis-flagget (AD-6) bare finnes ett sted. Eirik vurderte startlista og beholdt også gulvvask, fordi den er lett å glemme. (S11, PR #2) | `epics.md` Story 2.1 |
| 12 | KI låste FastAPI til 0.149.0 fordi arkitekturen sa «latest 0.14x», selv om 0.162.0 fantes. | Vi spurte om fordeler og ulemper og bestemte at «0.14x» bare var et øyeblikksbilde fra da arkitekturen ble skrevet. Vi bruker nyeste versjon og rettet arkitekturen med en datert merknad. (K25) | `ARCHITECTURE-SPINE.md` Stack, `backend/pyproject.toml` (Story 1.1) |
| 13 | KI foreslo tre åpne valg i spec-en for Story 1.1 (pip eller uv, appnavn, fanelinje). | Vi ba om fordeler og ulemper før vi valgte uv, beholdt «Husly» foreløpig og valgte et minimalt skall uten fanelinje. Ansvaret for fanelinjen ble notert som utsatt arbeid, så det ikke blir glemt. (K25) | Spec Story 1.1, `deferred-work.md` |

## Kvalitetssikring av KI-generert innhold (reviews)

Vi har bedt KI om uavhengige gjennomganger av sitt eget arbeid før dokumentene ble ferdigstilt, og vi har tatt stilling til funnene.

| Dokument | Review | Funn | Utfall |
|---|---|---|---|
| PRD | [`review-rubric.md`](../../_bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/review-rubric.md) | Rollen «Owner» var ikke avstemt med de tre rollene. KI-assistenten manglet sikkerhetskrav. Risikoen ved stort omfang var ikke håndtert med en prioritert kuttrekkefølge. | «Owner» ble fjernet fra rollemodellen, krav om disclaimer ble lagt til, og en foreløpig kuttrekkefølge ble lagt inn (`prd.md` OQ-1). Faglærer påpekte senere den samme omfangsrisikoen, og den følges nå opp med trinn 1/2. |
| UX | [`review-accessibility.md`](../../_bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/review-accessibility.md) | 15 funn (1 kritisk, 4 høye). Blant annet ga success-fargen #2F9E6E kontrast 3,37:1 og warning-fargen #D98A2B 2,76:1, under WCAG AA-kravet på 4,5:1. Zoom og reflow manglet. | Fargene ble mørknet til #267F59 og #9E641F (≥ 4,5:1), se `DESIGN.md`. |
| Arkitektur | [`review-adversarial.md`](../../_bmad-output/planning-artifacts/architecture/architecture-prosjektoppgave-ibe160-2026-10-04/reviews/review-adversarial.md) + rubric og versjonssjekk | 2 kritiske og 5 høye funn. Eksempel: bildebevis ble lagret per `Task`, mens datamodellen var per `TaskInstance`. Da ville utleier sett feil bilde etter andre utførelse. | `PhotoEvidence` gjort 1:1 med `Task` med peker til siste instans, se `ARCHITECTURE-SPINE.md`. |
| Spec Story 1.1 | Uavhengig gjennomgang før godkjenning ([Review Triage Log](../../_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md#review-triage-log)) | 9 funn, 2 høye. Spec-en ville gitt kode som så riktig ut, men ikke virket (se under). | Alle 9 rettet i spec-en før koden ble skrevet. |
| Kode Story 1.1 | Tre parallelle reviewere: Blind Hunter, Edge Case Hunter og Verification Gap (samme logg) | 42 funn. Etter at hvert funn ble sjekket mot koden: 14 grupper rettet, 11 avvist med begrunnelse, 1 utsatt og 2 håndtert i PR-en. | Rettet før PR. Testene økte fra 91 til 138. |

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
| Story 1.6 (lokal kjøring) krevde KI-tjenestens mock-modus, men KI-tjenesten bygges først i Story 5.1. Denne forover-avhengigheten kom inn med KI-forslaget i PR #1. | Readiness-sjekken i `bmad-sprint-planning` (S11). | Mock-kravet flyttet til Story 5.1, og seed-data utvides av 1.3 og 2.1 (`546d913`, PR #2) |
| CORS var låst til Vercel-adressen, så innlogging ville feilet ved lokal kjøring (FR-22). | Readiness-sjekken i `bmad-sprint-planning` (S11). | `CORS_ORIGINS` fra miljøvariabel, i arkitektur AD-7 og Story 1.2 (`1059cb5`, `546d913`, PR #2) |
| Spec-en for Story 1.1 krevde brytepunkter i `@media` og at token-testen skulle stoppe alle faste px-verdier. CSS tillater ikke `var()` i `@media`, så kravene motsa hverandre. | Gjennomgang av spec-en før godkjenning (K25). | Brytepunkter i `em` og egne tokens for trykkflate, fokus og skygge (`02925b9`, `6c529fd`) |
| Spec-en lot service workeren bygges som en vanlig Vite-inngang. Da får den et filnavn med hash i `/assets/` og styrer ikke appen. | Gjennomgang av spec-en før godkjenning (K25). | Bygges som `/service-worker.js` i roten og registreres bare i produksjonsbygg (`a780e33`) |
| Med vanlig `disabled` kan ikke primærknappen få fokus, så grunnen til at den er deaktivert blir aldri lest opp (UX-DR4). | Gjennomgang av spec-en før godkjenning (K25). | `aria-disabled` og ignorerte klikk, med test (`6c529fd`) |
| Token-testen så ut til å håndheve AD-13, men slapp gjennom `margin: -12px`, `style={{ padding: 12 }}` og `letter-spacing`. | Edge Case Hunter og Blind Hunter i kodegjennomgangen (K25). | Reglene er utvidet, med testtilfeller for hver (`02925b9`) |
| Installasjonsmeldingen viste Safari-instrukser til Chrome, Firefox og Instagram på iPhone. Et dobbelttrykk på «Installer» ga en uhåndtert feil. | Blind Hunter og Edge Case Hunter (K25). | Bare iOS Safari får instruks, og `prompt()` brukes én gang og feil fanges (`a780e33`) |
| Node-kravet «22 eller nyere» var for løst. Vitest 5 krever `^22.12`, og jsdom krever `^22.22.2 \|\| ^24.15.0`. Rettingen KI-en først foreslo for Node-versjonen var også for løs. | Blind Hunter fant første feil. Subagenten som rettet koden fant den andre ved å sjekke låsefila (K25). | `engines` og README bruker det strengeste kravet fra avhengighetene (`02925b9`, `2bd90bf`) |

## Ekstern tilbakemelding

Faglærers tilbakemelding på brief (06.10) pekte på stort omfang, utestbare suksesskriterier og at sensor ikke kan kjøre appen lokalt. Se [`tilbakemelding-product-brief.md`](../../_bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/tilbakemelding-product-brief.md). Hvordan vi følger dette opp, dokumenteres i oppdateringene av brief, PRD, arkitektur og epics.
