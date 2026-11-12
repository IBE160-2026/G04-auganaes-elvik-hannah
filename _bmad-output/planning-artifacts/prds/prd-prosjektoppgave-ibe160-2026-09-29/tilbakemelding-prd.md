# Tilbakemelding på PRD

| | |
|---|---|
| **Gruppe** | G04 – G04-auganaes-elvik-hannah |
| **PRD vurdert** | `_bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/prd.md` (status `final`, sist endret 2026-11-09, commit 00225e9) |
| **Dato** | 2026-11-12 |
| **Type** | Formativ tilbakemelding, ikke karakter |

## 1. Samlet inntrykk

Dette er en sterk PRD med tydelig tese (Landlord–Tenant-hierarkiet som strukturell forskjell), testbare konsekvenser under nesten alle FR-er og ærlig scope. Risikoen er at Trinn 2 er stort mens beslutningen om hva som kuttes fortsatt står som «pending team validation». I tillegg blander noen krav inn implementasjonsdetaljer og endringshistorikk, og noen få konsekvenser er fortsatt for vage til å bli testtilfeller.

## 2. Dette fungerer godt

- **Testbare konsekvenser og sporbare SM-er (§4, §7).** FR-9 sier at neste frist regnes fra faktisk utførelse, «not from the original due date», med eksempelet 30 dager og 2 dagers forsinkelse. SM-1 til SM-8 er skrevet slik at de kan bli automatiske tester, og hver peker tilbake til FR-ene den validerer.
- **Ærlig scope (§5, §6).** Non-Goals sier hva som er permanent («a permanent non-goal, not a v1 limitation») og hva som er utsatt. Delingen i Trinn 1 og Trinn 2 gjør at det finnes en komplett app selv om Trinn 2 ikke blir ferdig.
- **KI og kjørbarhet er tenkt inn.** FR-14 krever synlig forbehold om at KI kan ta feil, spesielt ved kjemikalier, og mock-svar uten nøkkel. FR-22 gjør at andre kan kjøre appen uten gruppens kontoer.

## 3. Oversikt per dimensjon

| Dimensjon | Vurdering | Kort begrunnelse |
|---|---|---|
| Beslutningsklarhet | god | Åpne spørsmål løses med dato og begrunnelse (Q2, Q3). Q1 og Q4 er fortsatt åpne i et dokument med `status: final`. |
| Substans | sterk | Personaene styrer reisene og FR-ene. Ingen NFR-boilerplate, bortsett fra «reliably enough» i Notification reliability. |
| Strategisk sammenheng | god | Tesen er klar. Men Target User sier at husholdningen er primærbruker i Trinn 1, mens det som skiller produktet ligger mest i Trinn 2 (foto, dashbord, utleiervarsler). |
| Testbarhet | god | De fleste FR-er har målbare konsekvenser. FR-4, FR-11, FR-15 og FR-16 har vage formuleringer. |
| Scope og avgrensning | god | Non-Goals og trinn er tydelige. Trinn 2 har 10 av 24 FR-er, og kuttlinjen er ikke bestemt. |
| Brukbarhet for neste fase | god | Glossar og ID-er er stort sett konsistente. Se kapittel 5 om utdatert FR-antall og noen begreper uten definisjon. |
| Formtilpasning | sterk | UJ-er med navngitte hovedpersoner passer et produkt med flere roller. UJ-4 er kort, og det er riktig. |

## 4. Viktigste forbedringer

### 4.1 Trinn 2 er stort, og kuttlinjen er ikke bestemt
- **Alvorlighet:** høy
- **Hvor:** §8 Q1 «provisional cut order … pending team validation», §6 Trinn 2
- **Problem og hvorfor det betyr noe:** Trinn 2 inneholder push (FR-10–13), full chat (FR-15), onboarding-guide (FR-16), foto (FR-18/19) og dashbord (FR-20), og fristen er midt i desember. Rekkefølgen for kutt er foreslått, men ikke vedtatt. UJ-1 og UJ-3 forutsetter dessuten Trinn 2 (UJ-1 starter med «a push notification», UJ-3 handler om målrettet varsel og foto), uten at det står hvilke steg som finnes i Trinn 1.
- **Forslag:** Vedta kuttlinjen og sett dato, f.eks. «Q1 er avgjort: FR-10, FR-12, FR-13, FR-18 og FR-19 er Trinn 2 (må). FR-15, FR-16, FR-11 og FR-20 er Trinn 2 (hvis tid), kuttet i denne rekkefølgen.» Legg til en linje per UJ om hva som virker i Trinn 1, f.eks. «UJ-1 i Trinn 1: Peter åpner appen selv, uten push».

### 4.2 Vage konsekvenser som ikke kan bli testtilfeller
- **Alvorlighet:** høy
- **Hvor:** FR-11 «rarely or never … several times», §8 Q4, FR-16 «receives or can access a guide referencing their specific Home/unit type», FR-4 «never unclassified»
- **Problem og hvorfor det betyr noe:** En story kan ikke skrives mot «several times». «Unit type» er heller ikke definert. FR-4 tester at klassifisering finnes, men ikke at anbefalingen er riktig.
- **Forslag:** FR-11: «Gitt minst to Members og en gjentakende delt oppgave: hvis Member B har 0 av de siste 3 utførelsene, sendes en målrettet påminnelse kun til B.» Det besvarer også Q4. FR-4: «Gitt oppgavetypen "rengjøre sluk" er anbefalt klassifisering Must.» Definer `unit type` i glossaret (f.eks. enkeltbolig, kollektiv, leilighet), eller si hva guiden faktisk må inneholde.

### 4.3 KI-feil, kostnad og data til ekstern tjeneste er ikke beskrevet
- **Alvorlighet:** medium
- **Hvor:** FR-14, FR-15, «Feature-specific NFRs» i §4.5
- **Problem og hvorfor det betyr noe:** Forbehold og mock er dekket. Men hva brukeren ser når KI-tjenesten feiler, er treg eller kvoten er brukt opp, står ikke. Det samme gjelder om antall KI-kall begrenses, og hvilke data som sendes til den eksterne tjenesten. «Returns an immediate answer» har ingen grense.
- **Forslag:** Legg til: «Hvis KI-kallet feiler eller tar over 10 sekunder, viser "?" en feilmelding og knappen kan prøves på nytt. Appen krasjer ikke.» Og: «Bare oppgavens navn og type sendes til KI-tjenesten, ingen navn eller e-poster.» Si også hvor mange kall per bruker per dag dere tillater, hvis det er en grense.

### 4.4 Endringshistorikk og kode ligger inne i kravene
- **Alvorlighet:** medium
- **Hvor:** FR-3 `[REVISED 2026-11-08]` (nevner `domain/homes.fr3_violations`), FR-8 `[REVISED 2026-11-09]` («409», filsti, «decisions by …»), FR-22 (`GEMINI_API_KEY`, VAPID)
- **Problem og hvorfor det betyr noe:** PRD-en skal være en stabil kilde for UX, arkitektur og stories. Når kravene blandes med story-numre, funksjonsnavn og HTTP-koder, blir den vanskeligere å lese, og kravteksten og koden kan komme ut av takt. Sporbarheten dere bygger via `sprint-change-proposal` er god, men hører hjemme der.
- **Forslag:** Behold én kort linje per revisjon («Endret 2026-11-09: se sprint-change-proposal-2026-11-09») og skriv kravet rent. FR-8 kan bli: «Frekvens velges blant faste intervaller (7, 14, 30, 42, 60, 90, 182, 365 dager).» Flytt miljøvariabelnavn til arkitektur.

### 4.5 SM-er tester regler som ikke står i FR-ene
- **Alvorlighet:** medium
- **Hvor:** SM-5 «an expired or used link shows a clear message», SM-6 «cannot read or change another Home's data», SM-9
- **Problem og hvorfor det betyr noe:** FR-2 sier ikke når en lenke utløper eller om den kan brukes flere ganger. FR-3 dekker skriving til låste felt, men ikke lesetilgang mellom Homes. En story bygger på FR-ene, så reglene kan bli oversett. SM-9 samler fire ulike tester i ett punkt.
- **Forslag:** Legg til i FR-2: «Lenken gjelder i 7 dager og kan brukes én gang. En utløpt eller brukt lenke gir en tydelig melding.» Legg til i FR-3: «Et Member kan ikke lese eller endre data i et Home de ikke er medlem av.» Del SM-9 i fire.

## 5. Mekaniske funn

- §0 sier «FR-1 through FR-22», men PRD-en har FR-1 til FR-24. FR-23 og FR-24 ligger midt i seksjonene (4.1, 4.3) og ikke sist.
- Begreper som brukes, men ikke står i glossaret: `Household Home`, `Landlord Home`, `Task Setup`, `Portfolio Dashboard`, `unit type`, `Trinn`.
- Assumptions Index sier at mekanismen for Photo Evidence er «undecided», men FR-24 og SM-9 («flagged eligible») forutsetter allerede en eligible-liste. Oppdater antakelsen.
- «Privacy Constraints» og «Cross-Cutting NFRs» ligger etter Assumptions Index, uten nummer. «Product's own support staff» (FR-19) finnes neppe i et kursprosjekt. Personvern for brukerkontoer er ikke nevnt.
- `status: final`, men Q1 og Q4 er åpne.

## 6. Før dere går videre

**Må avklares nå:** kuttlinjen for Trinn 2 (4.1), FR-11-regelen og Q4 (4.2), feil- og kostnadsoppførsel for KI (4.3), lenkeregler i FR-2 (4.5).

**Kan vente:** breakpoint-verdier (UX), eligible-liste for Photo Evidence, de langsiktige signalene SM-12 til SM-14.

**Oppfølging av brief-tilbakemeldingen: ja.** Trinn 1/Trinn 2 (§6), testbare SM-er (§7), husholdning som primærbruker (§3) og lokal kjøring (FR-22) er alle på plass. Personvern for brukerkontoer er det som gjenstår.

## 7. Refleksjonsspørsmål

1. FR-11 sier «rarely or never», og Q4 er åpen. Hvordan ville dere sjekket om en KI-foreslått terskel faktisk gir riktig oppførsel, og hvem avgjør hva «rettferdig» betyr?
2. Dere har endret PRD-en flere ganger etter at KI-assistert utvikling har pågått. Hva tok dere med fra koden og tilbake til kravene, og hvordan sjekket dere at kravteksten fortsatt stemmer med det som er bygget?

_Vurdert mot kvalitetsrubrikken i bmad-prd. Dette er veiledning, ikke sensur._
