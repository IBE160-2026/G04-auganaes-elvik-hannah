# Tilbakemelding på product brief

| | |
|---|---|
| **Gruppe** | G04 – G04-auganaes-elvik-hannah |
| **Product brief** | `_bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/brief.md` (commit `75186a6`) |
| **Tilbakemelding fra** | Faglærer i IBE160 (utarbeidet med KI-støtte) |
| **Dato** | 2026-10-06 |

## Samlet vurdering

- **Godt utgangspunkt med justeringer.** Gruppen kan gå videre og innarbeide punktene under.

Vi har vurdert briefen for «AI-Driven Household Task App» (Husly), sist oppdatert 2026-10-04. Vi har også sett at dere allerede har PRD, UX-spesifikasjon, arkitektur og `epics.md` med 6 epics og 20 historier. Det er bra fremdrift. Kommentarene gjelder briefen, men noen av dem bør også føres videre inn i PRD og arkitektur.

**Det som er bra:**

1. Problemet er konkret og godt avgrenset: uregelmessige oppgaver uten fast rytme, som å vaske badet grundig eller avkalke vannkokeren, blir glemt. Dere viser hva det koster i kollektiv (mugg, irritasjon og rettferdighet) og for utleier (reparasjoner og depositumskonflikter).
2. «Home»-mekanismen med must/should-oppgaver og låste oppgaver for leietaker er en tydelig og gjennomtenkt kjerne, og dere er ærlige om at fortrinnet ligger i tilpasning til et segment og ikke i teknologi. Det er også klokt at betaling, Hybel-integrasjon og vurderinger er satt som «out of scope».

**De viktigste endringene:**

1. Omfanget for v1 er stort. Det dekker fire segmenter, tre roller, invitasjoner, anbefalte frekvenser, push-varsler med egen kanal fra utleier, KI-chat og responsivt design. Dere skriver selv at KI-boten og rollemodellen er de tyngste delene. Definer en minimal kjerneflyt som skal være ferdig og stabil først, og prioriter resten.
2. De akademiske suksesskriteriene er for overordnede til å teste («the core loop … needs to actually function end-to-end»). Produktkriteriene om anmeldelser, færre konflikter og færre depositumskonflikter kan ikke måles i emnet. Legg til konkrete, funksjonelle kriterier.
3. Lag en plan for at sensor kan kjøre appen lokalt. Arkitekturen bygger på en delt Supabase-database, Render, Vercel, cron-job.org og Google Gemini. Det betyr at appen i dag forutsetter gruppens kontoer og nøkler.

## Vanskelighetsgrad og gjennomførbarhet

### Vurdert vanskelighetsgrad

- **Vanskelig**

**Sammenlignbart med:** I kjernen ligner ideen på 6) To-do-liste med smarte etiketter (enkel). Roller med låste rettigheter, invitasjoner, web push med planlagte jobber og KI-chat løfter likevel v1 opp på nivå med de vanskelige forslagene, for eksempel 3) KI-styrt simulering av prosjektledelse. Det skyldes antall moduler og integrasjoner, ikke tung fagdomenelogikk.

**Begrunnelse:**

| Faktor | Nivå (lav / middels / høy) | Kommentar |
|---|---|---|
| Domenelogikk – hvor mange og hvor kompliserte regler og beregninger må stemme? | middels | Regler for frekvens, forfall, omplanlegging etter avkrysning, must/should og «fairness nudge» må stemme. Reglene er forståelige og kan testes. |
| Datamodell – antall entiteter og relasjoner mellom dem | høy | Epics-dokumentet lister rundt tolv entiteter (Home, Membership, InviteLink, Task, TaskInstance, PhotoEvidence, PushSubscription osv.) med rolle per hjem. |
| Brukere, roller og innlogging | høy | Tre roller (Household Member, Landlord, Tenant) med rettigheter som må håndheves på serveren, og JWT med refresh-token. |
| KI-funksjonalitet i appen, f.eks. kall til språkmodell, prompts i koden og håndtering av usikre svar | middels | Hurtigsvar via «?» og full chat med oppgaven som kontekst. Det er avgrenset, men svarene må ha ansvarsfraskrivelse og håndtere feil. |
| Integrasjoner og eksterne tjenester, f.eks. API-er, betaling og e-post | høy | Gemini, Web Push (PWA og service worker, med begrensninger på iOS), ekstern cron, Supabase Storage og hosting på tre plattformer. |
| Sanntid, samtidighet eller flere brukere som påvirker hverandre | middels | Flere medlemmer deler og krysser av de samme oppgavene, og varsler sendes til andre brukere. |
| Filhåndtering, f.eks. opplasting, PDF-lesing og eksport | middels | Fotodokumentasjon står i epics (Epic 4), men ikke i briefen. |
| Sikkerhet og personvern | middels | Brukerkontoer, leietakerforhold og bilder fra private hjem. Det bør stå i briefen hvordan dette håndteres. |

**Hva vanskelighetsgraden betyr for dere:**

- _Vanskelig:_ Et vanskelig prosjekt gir større mulighet for toppkarakter, men også større risiko. Definer en minimal versjon som sikkert kan bli ferdig, og legg resten i tydelige trinn etterpå. For dere kan det være: hjem, invitasjon, roller, must/should-oversikt, avkrysning og omplanlegging. Push, fotodokumentasjon og utleierdashbord kommer i senere trinn.

### Gjennomførbarhet med BMAD og Claude Code

Dere skal planlegge med BMAD (product brief → PRD → arkitektur → epics og stories) og implementere med Claude Code. Vurderingen under tar hensyn til at det må være tid til hele denne flyten, og til testing, retting og README til slutt.

| Spørsmål | Vurdering (OK / risiko / stor risiko) | Kommentar |
|---|---|---|
| **Tid og omfang** – kan v1 realistisk bli ferdig og stabil i løpet av semesteret, med tid til flere iterasjoner? | risiko | 20 historier over 6 epics innen midten av desember er mye for tre nybegynnere, særlig når både push og KI står i v1. |
| **BMAD-flyten** – er briefen konkret nok til at PRD, arkitektur og stories kan lages uten store hull, og blir det overkommelig mange stories? | OK | Briefen var konkret nok til at dere har kommet gjennom hele flyten. Merk at fotodokumentasjon og utleierdashbord har kommet inn senere uten at briefen nevner dem. Oppdater briefen eller begrunn tillegget. |
| **Egnet for Claude Code** – bruker løsningen en vanlig, godt dokumentert teknologistakk som Claude Code håndterer godt, eller krever den nisjeteknologi, spesialmaskinvare eller mye manuell konfigurasjon? | risiko | FastAPI og React er godt egnet. Web Push, service worker og ekstern cron er derimot krevende å sette opp og feilsøke. |
| **Kontroll på KI-ens arbeid** – kan gruppen selv avgjøre om koden gjør det riktige? Krever domenet kunnskap gruppen ikke har, f.eks. avanserte beregninger eller fagregler, så er det vanskelig å kvalitetssikre. | OK | Domenet er hverdagslig, og dere kan selv avgjøre om en oppgave er forfalt eller om en leietaker får endret en låst oppgave. |
| **Testbarhet** – finnes det tydelige regler og forventede resultater som tester kan skrives mot? | OK | Rolle- og forfallsreglene egner seg godt for automatiske tester, for eksempel at leietaker får 403 ved endring av must-oppgave. Push og KI-svar må testes med mock-objekter. |
| **Kjørbar for sensor** – kan appen kjøres lokalt etter README, uten gruppens nøkler, betalte kontoer eller egen infrastruktur? | stor risiko | Delt Supabase-instans, Render, Vercel og cron-job.org betyr at sensor i dag ikke kan kjøre appen uten deres oppsett. |
| **Avhengigheter og kostnader** – krever løsningen betalte API-er, f.eks. språkmodeller, og finnes det en plan for kostnad, testmodus eller mock-data? | risiko | Gemini og gratisnivåene er gratis å starte med, men krever nøkler og kontoer. Det trengs en testmodus. |

**Konklusjon om gjennomførbarhet:**

- **Gjennomførbart med justert omfang.** Se forslagene under.

**Forslag til justering av omfang eller vanskelighetsgrad:**

1. Del v1 i to trinn. Trinn 1 er hjem, invitasjon, roller, must/should, anbefalt frekvens, avkrysning og omplanlegging, pluss KI-hurtigsvar. Trinn 2 er push-varsler, landlord-broadcast, fotodokumentasjon og porteføljedashbord. Da har dere en komplett app selv om trinn 2 ikke blir ferdig.
2. Gjør appen kjørbar lokalt: lokal database (SQLite eller Postgres i Docker) med Alembic-migreringer og seed-data, `.env.example` og en «mock»-modus for Gemini og push som brukes når nøkler mangler. Hosting kan dere gjerne beholde i tillegg.

## Hvorfor product brief er viktig for mappen

Product brief er utgangspunktet for PRD, arkitektur, stories og til slutt koden. Del 1 av mappen vurderes blant annet på om sensor kan følge en sporbar vei fra plan til ferdig app. Den vurderes også på om appen gjør det dere har beskrevet, om den er testet, om den er godt designet, og om den kan kjøres etter README. Et uklart, for stort eller for lite brief gjør alt dette vanskeligere senere. Det er mye enklere å rette nå enn sent i semesteret.

## 1. Gjennomgang av briefens deler

| Del av brief | Status | Kommentar |
|---|---|---|
| Executive Summary – er det klart hva appen er, og hvilket problem den løser? | OK | Klart hva appen er (delt «home» med must/should) og hvilket problem den løser (uregelmessige oppgaver som glemmes). |
| The Problem – er problemet konkret, med reelle situasjoner og brukere? | OK | Gode eksempler fra kollektiv og utleie. Dere er ærlige om at det bygger på egen erfaring og ikke på brukerundersøkelser. |
| The Solution – beskriver løsningen brukeropplevelsen, ikke bare teknologi? | OK | Beskriver hva brukeren ser og gjør, for eksempel «?»-ikonet og anbefalt frekvens som brukeren godkjenner. |
| What Makes This Different – er vurderingen ærlig og realistisk? | OK | Konkurrenter er navngitt (Sweepy, OurHome, Tody, Flatastic, Hybel), og dere sier ærlig at det ikke finnes noen teknisk «moat». |
| Who This Serves – er primærbrukerne tydelige, og vet vi hva de trenger? | Juster | Fire segmenter, og utleier omtales som «the primary user». Designet blir enklere hvis dere velger én primærbruker for v1, for eksempel kollektiv eller utleier med leietakere. |
| Success Criteria – kan kriteriene faktisk sjekkes eller testes? | Juster | Dette bør rettes før implementeringen starter. Det akademiske kriteriet er for overordnet, og produktkriteriene (anmeldelser, færre konflikter) kan ikke måles i emnet. Legg til kriterier som «en leietaker kan ikke endre frekvens eller status på en must-oppgave satt av utleier» og «når en oppgave krysses av, får den ny forfallsdato ut fra frekvensen». |
| Scope – er det klart hva som er med i første versjon, og hva som ikke er det? | Juster | Det er tydelig hva som er inne og ute, men «in scope» er stort. Prioriter innenfor v1, og ta inn fotodokumentasjon og dashbord som nå står i epics. |
| Vision – henger visjonen sammen med resten uten å blåse opp omfanget? | OK | Abonnement, Hybel-integrasjon og bredere boligforvaltning er tydelig merket som fremtidige retninger. |

## 2. Utgangspunkt for del 1 av mappen

Punktene følger kriteriene i sensorveiledningen for del 1. Vektene i parentes viser hvor mye hvert kriterium teller i del 1.

| Kriterium i del 1 | Hva briefen bør legge til rette for | Status | Kommentar |
|---|---|---|---|
| **1. Prosess og KI-styring** (30 %) | Brief som er presis nok til at PRD og stories kan bygges direkte på den, slik at krav kan spores fra brief til kode. | OK | Dere har allerede en sporbar kjede fra brief til PRD, UX, arkitektur og epics, med beskrivende commits. Fortsett slik, og oppdater briefen når omfanget endres. |
| **2. Funksjonalitet og omfang** (20 %) | Realistisk omfang for gruppen og semesteret: en tydelig kjerneflyt som kan bli ferdig og stabil, og nok innhold til å vise reell funksjonalitet. | Juster | Nok funksjonalitet, men en risiko for at mye blir halvferdig. Prioriter kjerneflyten. |
| **3. Kvalitetssikring og testing** (15 %) | Suksesskriterier og funksjoner som er konkrete nok til å bli testtilfeller. | Juster | Reglene for rolle, forfall og omplanlegging egner seg godt for tester, men det må komme fram i suksesskriteriene. |
| **4. Design og brukeropplevelse** (10 %) | Tydelige brukere og brukssituasjoner som designet kan bygges rundt, gjerne med de viktigste skjermbildene eller flytene skissert. | OK | UX-spesifikasjonen (DESIGN.md og EXPERIENCE.md) med tilgjengelighet og breakpoints gir et godt grunnlag. |
| **5. Kodekvalitet og arkitektur** (10 %) | Teknologivalg som er begrunnet og ikke mer komplekse enn appen trenger. | Juster | Tre hostingplattformer, ekstern cron og PWA er mye infrastruktur for et studentprosjekt. Vurder om noe kan forenkles. |
| **6. README og kjørbarhet** (10 %) | Løsning som andre kan kjøre lokalt uten betalte kontoer, og uten tilgang til gruppens egne tjenester og nøkler. | Juster | Dette bør inn i arkitekturen før implementeringen starter. Planlegg lokal kjøring med egen database, seed-data og mock av Gemini og push, slik at sensor ikke er avhengig av deres Supabase-instans. |
| **7. Ryddighet i repoet** (5 %) | En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge. | Juster | Mange nøkler (Supabase, Gemini, VAPID og JWT-hemmelighet) skal holdes ute av repoet. Lag `.env.example` tidlig og sjekk `.gitignore`. |

## 3. Neste steg for gruppen

1. Oppdater Success Criteria i briefen med 5–8 funksjonelle kriterier som kan bli testtilfeller, og flytt anmeldelser og konfliktreduksjon til visjonen.
2. Marker i briefen og i epics hvilke historier som utgjør minimal v1 (trinn 1), og hvilke som er trinn 2. Begrunn tilleggene fotodokumentasjon og porteføljedashbord.
3. Legg inn i arkitekturen et lokalt kjøreoppsett med lokal database, seed-data og mock-modus for KI og push, og beskriv det i README fra første historie.

Oppdater product brief i repoet når dere har gjort endringene, slik at historikken viser hvordan planen utviklet seg. Det er en del av prosessen sensor ser etter.
