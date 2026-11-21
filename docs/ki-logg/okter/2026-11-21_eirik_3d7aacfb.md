# KI-økt 2026-11-21 – Eirik

- **Økt-ID:** `3d7aacfb-6e1b-4f4e-8e34-1d9c0372fe11`
- **Tidsrom:** 2026-11-21 19:05 – 2026-11-21 21:05
- **Verktøy:** Claude Code
- **Antall prompts:** 20

Generert automatisk av `scripts/ki-logg/eksporter_okter.py`. Promptene er gjengitt ordrett;
personlige stier og e-postadresser er fjernet. Sammendrag av økta står i `docs/ki-logg/README.md`.

## Commits gjort mens økta var aktiv

- `536f5ea` 2026-11-21 19:15 (Eirik) Story 6.1: portefølje for utleier med én rad per hjem (FR-20)
- `c3a24a1` 2026-11-21 19:20 (Eirik) Story 6.1: rettinger etter kodegjennomgang (tre reviewere)
- `35be20c` 2026-11-21 19:33 (EirikAuganaes) Merge pull request #87 from IBE160-2026/story/6-1-portefolje
- `19c79a9` 2026-11-21 19:34 (Eirik) Status: Story 6.1 ferdig (PR #87), alle stories gjort
- `71c25f5` 2026-11-21 19:51 (Eirik) Status: A4 godtatt som kjent grense i AD-5 (Blob-cache 60 s)
- `eb81191` 2026-11-21 19:52 (Eirik) Epic 6-retrospektiv, Gemini-røyktest på Production og KI-korrigering for 6.1
- `ff1b545` 2026-11-21 19:53 (Eirik) KI-logg: økt 21.11 (Story 6.1, retrospektiv og røyktest)
- `b2fdb76` 2026-11-21 19:53 (Eirik) Logg: story-6-1-portefolje
- `131e373` 2026-11-21 19:55 (Eirik) Påminnelse for Eirik og Steffen 22.11 (B1, Windows-test, skjermleser, layout, testdata)
- `e16ce7a` 2026-11-21 19:56 (Eirik) Epic 5-retrospektiv (akseptert med åpne punkter) og to nye tiltak (D1, D2)
- `192af59` 2026-11-21 20:00 (Eirik) Chatpolering (D1, Epic 5-retro): auto-scroll, makshøyde og mislykket melding blir stående
- `c720cdb` 2026-11-21 20:03 (EirikAuganaes) Merge pull request #88 from IBE160-2026/fix/5-2-chat-polering
- `7e95efe` 2026-11-21 20:05 (Eirik) D2: KI-stories sier hva KI-en ikke skal gjøre (CLAUDE.md og reviewkonvensjoner)
- `741f9c1` 2026-11-21 20:08 (EirikAuganaes) Merge pull request #89 from IBE160-2026/chore/d2-ki-ac-regel
- `8a0baf0` 2026-11-21 20:09 (Eirik) KI-logg: eksport av økten 21.11 (Story 6.1, retrospektiver, D1 og D2)
- `0e76000` 2026-11-21 20:14 (Eirik) Opprydding i deferred-work.md: utfall på 17 punkter og plan for resten
- `a0f5e06` 2026-11-21 20:17 (EirikAuganaes) Merge pull request #90 from IBE160-2026/chore/deferred-work-opprydding
- `cbdb8ec` 2026-11-21 20:21 (Eirik) Correct-course: kontosletting med anonymisering (FR-25, AD-17, Story 1.10)
- `38144e4` 2026-11-21 20:24 (EirikAuganaes) Merge pull request #91 from IBE160-2026/docs/correct-course-kontosletting
- `575357c` 2026-11-21 20:32 (Eirik) Story 1.10: slett konto med anonymisering (FR-25, AD-17)
- `39e324f` 2026-11-21 20:38 (Eirik) Story 1.10: rettinger etter kodegjennomgang (tre reviewere)
- `0c42f6b` 2026-11-21 20:40 (Eirik) Status: Story 1.10 ferdig (PR #93), kontosletting bygget
- `ecad752` 2026-11-21 20:40 (EirikAuganaes) Merge pull request #93 from IBE160-2026/story/1-10-kontosletting
- `54feb3f` 2026-11-21 20:43 (Eirik) Fotorobusthet: avkuttet JPEG avvises, mislykket fullføring setter gammelt bilde tilbake
- `ec1367f` 2026-11-21 20:47 (Eirik) Fotorobusthet: rettinger etter kodegjennomgang
- `cc3298f` 2026-11-21 20:50 (EirikAuganaes) Merge pull request #94 from IBE160-2026/fix/foto-robusthet
- `c989c6a` 2026-11-21 20:56 (Eirik) Småfikser fra deferred-work: e-post i små bokstaver, offline-melding, demo-markering m.m.
- `ad4f481` 2026-11-21 20:58 (Eirik) Småfikser: rettinger etter kodegjennomgang
- `21cbd0c` 2026-11-21 21:01 (EirikAuganaes) Merge pull request #95 from IBE160-2026/fix/smaating
- `639a314` 2026-11-21 21:10 (Eirik) Postgres-samtidighetstester for radlåsene, og lås for join mot kontosletting
- `2f688f0` 2026-11-21 21:12 (Eirik) invites.accept: den låste lenka leses på nytt med verdiene låsen ventet på
- `64caf75` 2026-11-21 21:14 (Eirik) SCRATCH: alle radlåser fjernet (mutasjonssjekk av Postgres-testene, skal ikke merges)

## Logg

### 1. Prompt · 2026-11-21 19:05

> fortsett

### 2. Svar på spørsmål fra KI · 2026-11-21 19:05

> "Hva vil du at jeg skal fortsette med?"="Story 6.1 portefølje (Recommended)".

### 3. Svar på spørsmål fra KI · 2026-11-21 19:07

> "AC og FR-20 sier «per Home og per enhet» og «bygningsliste», men modellen har bare Home (hver enhet er sitt eget Home, UJ-2), ingen bygning. Hva gjør vi?"="Én rad per Home (Recommended)", "Hva viser detaljpanelet (to kolonner på nettbrett/desktop) for valgt Home, og hva skjer ved trykk på rad på mobil?"="Forfalte Må-oppgaver + lenke (Recommended)", "Pull-to-refresh (UX-DR36): hvordan?"="Pull-gest + «Oppdater»-knapp (Recommended)".

### 4. Svar på spørsmål fra KI · 2026-11-21 19:08

> "Hva gjør vi med spec-en for Story 6.1?"="Godkjenn og fortsett (Recommended)".

### 5. Svar på spørsmål fra KI · 2026-11-21 19:16

> "Kodegjennomgangen i bmad-build bruker tre subagenter (Blind Hunter, Edge Case Hunter, Verification Gap). Får jeg starte dem?"="Ja, kjør alle tre (Recommended)".

### 6. Prompt · 2026-11-21 19:23

> Perfekt pusg og lag pr før bmad walktrough. Hva gjenstår?

### 7. Prompt · 2026-11-21 19:29

> sjekk CI først

### 8. Prompt · 2026-11-21 19:30

> start walkthrough

### 9. Prompt · 2026-11-21 19:33

> neste

### 10. Prompt · 2026-11-21 19:33

> netse

### 11. Prompt · 2026-11-21 19:33

> godkjenn og merge

### 12. Prompt · 2026-11-21 19:42

> Du får mandat til å gjøre gjenstående i den rekkefølgen du mener er best. Ved usikkerhet kan du konferere med meg.

### 13. Prompt · 2026-11-21 19:48

> Du skal ha internett nå

### 14. Svar på spørsmål fra KI · 2026-11-21 19:50

> "Gemini-røyktest av 5.2 (chat med historikk) og 5.3 (velkomstguide) krever en testkonto og testdata på det hostede nettstedet g04husly.vercel.app (delt Neon-database, ekte Gemini-nøkkel). Skal jeg gjøre det?"="Ja, på Production", "A4: Blob-cachen kan gi gammelt bilde i opptil 60 s etter at en leietaker erstatter bildet. Hva gjør vi?"="Godta som kjent grense (Recommended)", "B2: push-pålitelighet (tidsbudsjett per medlem, 401/403 fra gamle enheter, pushsubscriptionchange, ON DELETE, batching). Hva gjør vi?"="Vent til B1 er bekreftet".

### 15. Prompt · 2026-11-21 19:54

> Jeg og Steffen skal k

### 16. Prompt · 2026-11-21 19:55

> Jeg og Steffen skal jobbe sammen imorgen lag en påminnelse om punkt 1-2-3-4-5. Epic 5 retroperspektivet kan vi se på nå.

### 17. Prompt · 2026-11-21 19:58

> bygg D1 chatpoleringen nå. Hva er denne chatpoleringen?

### 18. Prompt · 2026-11-21 20:02

> sjekk CI og merge hvis grønn

### 19. Prompt · 2026-11-21 20:04

> Hva er D2?

### 20. Prompt · 2026-11-21 20:05

> Ja, skriv det inn i begge

### 21. Prompt · 2026-11-21 20:06

> merge PR #89

### 22. Prompt · 2026-11-21 20:09

> commit KI-loggen og push

### 23. Prompt · 2026-11-21 20:10

> Vakkert. Noe annet vi mangler som ligger i defered? Vi har fortsatt 2 - 3 uker og god tid.

### 24. Prompt · 2026-11-21 20:13

> Start med opprydding og correct-course for kontosletting. Du får mandat til å fikse alt her. Konferer med meg ved spørsmål

### 25. Svar på spørsmål fra KI · 2026-11-21 20:16

> "Jeg lager flere PR-er (opprydding #90, småfikser, fotorobusthet, Postgres-tester, kontosletting). Skal jeg merge hver PR selv når CI er grønn, eller vente på ditt ok per PR?"="Merge selv når CI er grønn".

### 26. Svar på spørsmål fra KI · 2026-11-21 20:20

> "En utleier med leietakere kan ikke bare forsvinne (FR-3: nøyaktig én utleier, FR-23: utleier kan ikke forlate hjemmet). Hva skjer når en utleier sletter kontoen sin?"="Må fjerne leietakerne først (Recommended)", "Når en husstandsbruker eller leietaker sletter kontoen: anonymisere brukerraden (navn blir «Tidligere medlem», e-post og passord fjernes, raden beholdes så historikken henger sammen), fjerne medlemskap, push-enheter, varslingshistorikk og KI-telling, og slette hjem som ikke har flere medlemmer (med bilder)? Er du enig?"="Ja, slik (Recommended)".

### 27. Prompt · 2026-11-21 21:05

> Ja, ta Postgres-samtidighetstestene

