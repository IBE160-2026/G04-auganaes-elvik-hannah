# Skjermlesersjekk (C1), 22.11

Én runde med skjermleser over det jest-dom ikke kan teste: hva som faktisk leses opp. Dette er punkt 4 i [`plan-eirik-steffen-2026-11-22.md`](plan-eirik-steffen-2026-11-22.md). Kildene til hvert spørsmål står i [`deferred-work.md`](../_bmad-output/implementation-artifacts/deferred-work.md) (Story 5.1, 3.4 og 6.1).

**Deling:** Eirik tar Mac og VoiceOver (del A–C), Steffen tar Windows og NVDA (del D–E). Del F er valgfri for den som har tid igjen.

## Oppsett

| | Mac (Eirik) | Windows (Steffen) |
|---|---|---|
| Skjermleser | VoiceOver, slå av/på med `Cmd+F5` | NVDA (start fra Start-menyen eller `Ctrl+Alt+N`) |
| Nettleser | Safari (VoiceOver er best tilpasset den), gjenta gjerne i Chrome | Chrome eller Firefox |
| Nyttig | `Ctrl+Option+U` åpner rotoren (overskrifter, lenker, skjemakontroller) | `NVDA+F7` viser elementlisten, `H` hopper mellom overskrifter |
| Se hva som sies | Bildetekstpanelet (Caption Panel), slått på i VoiceOver-verktøyet | Talevisning: NVDA-meny → Verktøy → Talevisning |

Slå på talevisning (eller skriv ned det som sies) mens du tester: «så ut til å virke» er ikke et resultat, ordlyden er det.

**Data:** Kjør `git pull`, `docker compose up -d --wait` og `cd backend && uv run python -m app.seed`. Eksempelbrukerne har passord `husly-demo`: Mari, Jonas, Kari (utleier), Anders (leietaker). Seed gjenskaper Kari, Jonas og Anders hvis de er slettet lokalt (Eirik slettet dem under nettlesersjekken 22.11). Bruk `npm run dev` på `http://localhost:5173` med backend på `:8000` (README «Kom i gang»).

## Del A: KI-popoveren «Spør KI» (Eirik, Story 5.1)

Logg inn som Mari, åpne en oppgave (f.eks. «Rens sluket») og knappen «Spør KI om «Rens sluket»».

- [ ] **A1.** Knappen leses som knapp med navnet «Spør KI om «Rens sluket»», og tilstanden (utvidet/skjult) sies.
- [ ] **A2.** Trykk den: sies noe mens svaret lastes (skjelettet er `aria-hidden`)? **Kjent spørsmål:** live-regionen ligger i et `hidden` panel, så teksten i det øyeblikket panelet åpnes kan bli stående uten å bli lest.
- [ ] **A3.** Leses selve svaret opp når det kommer, uten at du må navigere dit?
- [ ] **A4.** Leses ansvarsfraskrivelsen («KI kan ta feil …») og demo-merknaden?
- [ ] **A5.** Feilsituasjon: i nettleserens konsoll, kjør `window.__f=fetch;fetch=()=>Promise.reject(new TypeError('x'))`, trykk «Spør KI» på en annen oppgave og lytt. Feilteksten har `role="alert"` inne i en `aria-live="polite"`-region: leses den én gang, to ganger eller ikke i det hele tatt? Gjenopprett med `fetch=window.__f`.
- [ ] **A6.** Tastatur: kan du åpne, lese og lukke popoveren med bare tastaturet, og hvor havner fokus når den lukkes?

**Hvis A2 eller A5 feiler:** forslaget fra Story 5.1-reviewen er et visuelt skjult statuselement utenfor panelet og å droppe `role="alert"` der.

## Del B: Chatten «Spør mer» (Eirik, Story 5.2)

Fra svaret i popoveren: «Spør mer» (`/hjem/<id>/oppgaver/<id>/chat`).

- [ ] **B1.** Loggen er en `role="log"` med navnet «Spør KI om «…»». Leses nye meldinger opp når de kommer?
- [ ] **B2.** Send to meldinger etter hverandre. Leses begge svar? (Svarene fra mocken har lik tekst, så dette tester også at identisk tekst blir lest to ganger.)
- [ ] **B3.** Etter «Send»: hvor havner fokus? Koden setter det tilbake i feltet. Sies noe som forteller at meldingen gikk av gårde?
- [ ] **B4.** Mislykket melding (samme `fetch`-triks som A5): leses «Vi fikk ikke svar akkurat nå …» og er «Prøv igjen» nåbar med Tab?
- [ ] **B5.** Er ansvarsfraskrivelsen tilgjengelig uten å lete?

## Del C: Portefølje (Eirik, Story 6.1)

Krever en utleier med **to** utleiehjem. Seed gir bare Kari ett (Storgata 12): opprett et utleiehjem til som Kari (Innstillinger → Opprett nytt hjem → Utleiebolig, og sett opp oppgaver), se `docs/prov-appen.md` «Prøv porteføljen». Bruk et nettleservindu på minst 600 px (da er detaljkolonnen synlig).

- [ ] **C1.** Fanen «Portefølje» leses som en lenke i hovedmenyen, og gjeldende side sies («gjeldende side»/«current page»).
- [ ] **C2.** Hver rad leses med hjemmenavn og status i tekst («Forsinket», «Alt i orden»), ikke bare farge, og med om den er valgt (`aria-pressed`).
- [ ] **C3.** **Kjent spørsmål:** velg en annen rad. Kunngjøres det at detaljkolonnen har byttet innhold? Flyttes fokus? (Slik koden er nå er `aria-pressed` og at seksjonen byttes de eneste signalene.)
- [ ] **C4.** Leses detaljene (forfalte oppgaver med «N dager forsinket») i en fornuftig rekkefølge, og er «Administrer hjemmet» nåbar?
- [ ] **C5.** **Kjent spørsmål:** trykk «Oppdater». Leses «Oppdatert» opp? Trykk to ganger rett etter hverandre: leses den andre også?
- [ ] **C6.** Under 600 px (smalt vindu eller mobil): er raden en lenke til «Administrer hjemmet» og leses den slik?

## Del D: Bildeopplasting for leietaker (Steffen, Story 4.2)

Oppsett: logg inn som **Kari**, gå til «Administrer hjemmet» for Storgata 12 (`/hjem/<id>/utleier`), og krev bildebevis på «Rens sluket» under «Bildebevis». Logg så inn som **Anders** (andre nettleser eller privat vindu) og åpne «Rens sluket». Bruk et lite JPEG-bilde (under 3,5 MB).

- [ ] **D1.** Seksjonen leses med overskriften «Bildebevis» og forklaringsteksten («Utleieren krever et bilde …»).
- [ ] **D2.** Filvelgeren leses med navnet «Ta eller velg bilde» og som filvelger/knapp. Fungerer den med Enter/mellomrom?
- [ ] **D3.** Velg bildet: leses «Laster opp …» og så «Bilde lastet opp. Oppgaven er fullført.»? (Statusen ligger alltid i DOM-en og er `aria-live="polite"`.)
- [ ] **D4.** Tving en feil (for stort bilde eller en ikke-JPEG-fil): leses feilmeldingen (`role="alert"`) en gang? Er «Prøv igjen» nåbar?
- [ ] **D5.** Etter opplasting: sier noe at avkrysningen/oppgaven nå er fullført, eller må du finne det selv?

## Del E: Utleier ser bildet, og utleiers melding (Steffen, Story 4.3 og 3.4)

- [ ] **E1.** Som Kari: åpne «Rens sluket». «Bildebevis» leses med beskrivelsen og bildet har alternativ tekst «Bildebevis for oppgaven». Leses «Laster bildet …» mens det hentes?
- [ ] **E2.** Hvis bildet ikke finnes: leses «Ingen bilde er lastet opp ennå.»?
- [ ] **E3.** **Kjent spørsmål (Story 3.4):** på «Administrer hjemmet», send en melding til leietakerne to ganger med samme antall mottakere. Leses bekreftelsen («Sendt til N …») begge gangene? Koden nullstiller og setter meldingen i samme render, så regionen ser kanskje aldri en tom tilstand.

## Del F: Valgfritt (hvis det er tid)

- [ ] Fanelinja: «Oppgaver», «Portefølje», «Innstillinger» leses som en navigasjon («Hovedmeny») og gjeldende fane sies.
- [ ] Slett konto (Innstillinger): leses advarselen, feltet «Passord», og feilmeldingene «Skriv inn passordet ditt for å bekrefte.» og «Passordet stemmer ikke.»?

## Registrer resultatet

Skriv ned for hvert punkt: **OK**, **feil** (med det som faktisk ble lest) eller **uklart**. Bruk gjerne tabellen under, og legg den i denne fila.

| Punkt | Resultat | Det som ble lest / kommentar | Skjermleser og nettleser |
|---|---|---|---|
| A1 | | | |

Når runden er gjort:

1. **Funn** føres som GitHub-issues (én per rettelse, med branch og PR som vanlig), eller i `deferred-work.md` hvis dere godtar dem som kjente grenser. Skriv rettelsene på norsk i PR-en og noter KI-feil i [`korrigeringer.md`](ki-logg/korrigeringer.md).
2. **Lukk** de tre skjermlesersjekk-punktene i `_bmad-output/implementation-artifacts/deferred-work.md` (Story 5.1-popoveren, Story 3.4-bekreftelsen og porteføljens detaljkolonne) med `outcome:` og dato, og de åpne Epic 2-, 4- og 6-punktene i `sprint-status.yaml`.
3. Lukk C1 i `.logs/<bruker>/issues.md`, og skriv en linje om runden i [`ki-logg/README.md`](ki-logg/README.md).
