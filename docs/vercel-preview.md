# Teste en PR på Vercel-preview

Veiledning til den som tester en PR i nettleseren før merge (i praksis Eirik, som eier Vercel- og Neon-dashboardene). Den lokale kjøringen i [README](../README.md) er hovedveien og trengs ikke her; en preview er en ekstra sjekk av at koden også virker på Vercel med Neon.

## Hva en preview er

- Hver PR får en egen forhåndsvisning av appen på en egen adresse, bygget fra PR-ens branch (`vercel.json`: frontend og backend på samme domene, `/api` går til FastAPI).
- Hver preview får også en **egen Neon-gren** `preview/<branch-navn>`, laget fra `main`. Byggesteget kjører `alembic upgrade head` mot denne grenen, aldri mot produksjon. Grenen slettes av [en workflow](../.github/workflows/neon-preview-cleanup.yml) når PR-en lukkes eller merges.
- En stablet PR (for eksempel #46 på toppen av #44) bygges fra sin egen branch, så previewen har også koden og migreringene fra PR-en under.

## Viktig å vite før du tester

- **Det finnes ingen seed-brukere.** Seed-kommandoen nekter å kjøre på Vercel med vilje. Mari, Jonas, Kari og Anders finnes bare lokalt. På previewen registrerer du egne testkontoer.
- **Databasen er en kopi av `main`.** Den kan inneholde det som er registrert på produksjonsnettet. Bruk nye e-postadresser, for eksempel `test1@example.com`, og ikke ekte personopplysninger.
- **Alt du gjør, forsvinner** når PR-en lukkes og Neon-grenen slettes. Ingenting du gjør på en preview kan påvirke produksjon.
- Vercel Authentication er skrudd av for previews (valgt 01.11). Dukker det opp en Vercel-innlogging, er beskyttelsen slått på igjen: Project Settings → Deployment Protection.

## 1. Finn previewen

1. Åpne PR-en på GitHub og vent til sjekkene er ferdige. Alle CI-jobbene og Vercel-bygget skal være grønne.
2. Trykk **Details** ved Vercel-sjekken (eller **Visit Preview** i Vercel-kommentaren) for å åpne adressen. Den ser ut som `g04husly-git-<branch>-<team>.vercel.app`.
3. **Bruk alltid adressen fra PR-en du tester, aldri en gammel lenke.** Vercel beholder adressene til gamle previews, og de kan ligge i nettleserhistorikken. Når en PR er merget, slettes Neon-grenen, og en gammel preview svarer «Databasen svarer ikke» (503). I appen ser det ut som «Noe gikk galt» når du prøver å registrere deg eller logge inn.
4. Feiler Vercel-bygget, åpner du byggeloggen fra samme knapp. En feilende migrering stopper bygget, og da er det forrige versjon som står.

## 2. Sjekk at API-et og databasen lever

Åpne i nettleseren (eller `curl`):

- `<preview>/api/health`: svarer at API-et lever.
- `<preview>/api/health/db`: svarer `{"database":"ok"}`.

Svarer ikke `/api/health/db`, når ikke API-et Neon-grenen. Se Vercel → Deployments → Logs.

## 3. Sjekk migreringen i Neon

Dette er den viktigste sjekken for PR-er som endrer databasen.

1. Åpne [console.neon.tech](https://console.neon.tech), velg prosjektet og **Branches**. Velg grenen `preview/<branch-navn>`.
2. Åpne **SQL Editor** for den grenen og kjør `select * from alembic_version;`.
3. Verdien skal være den siste migreringen i PR-en. Sammenlign med `uv run alembic heads` lokalt, eller med filene i `backend/alembic/versions/`:

| PR | Siste migrering |
|---|---|
| #44 (Story 2.4 og 2.5) | `c4e1d2a7b9f3` |
| #46 (Story 2.6) | `d7a3b5c9e2f1` |

Står verdien på en eldre migrering, har bygget ikke kjørt den. Se byggeloggen.

## 4. Prøv funksjonen

Du trenger to brukere for å se delt status. Bruk to nettlesere, eller ett vanlig vindu og ett privat.

**Oppsett (én gang per preview):**

1. Vindu A: trykk **Opprett konto**, registrer `test1@example.com` med et passord du finner på, og opprett et hjem av typen **Husstand**.
2. Sett opp oppgavene (godta anbefalingene).
3. Åpne **Medlemmer og invitasjon**, lag en invitasjonslenke og kopier den.
4. Vindu B: åpne lenken, registrer `test2@example.com` og bli med.

**Story 2.4 og 2.5 (PR #44):**

1. A krysser av en oppgave. B trykker **Oppdater** og ser «Fullført i dag av …».
2. Neste frist er avkrysningsdatoen pluss hyppigheten.
3. Boksen kan ikke angres. Et nytt trykk gjør ingenting.

**Story 2.6 (PR #46):**

1. A trykker **Legg til oppgave**, velger en egen oppgave og lagrer. Oversikten viser «La til «X».».
2. Prøv et navn som allerede finnes (også med andre store og små bokstaver). Meldingen vises ved navnefeltet.
3. Åpne oppgaven og trykk **Fjern oppgaven**, og bekreft. Oversikten viser «Fjernet «X».», og B ser at oppgaven er borte etter **Oppdater**.
4. Legg til den samme katalogoppgaven igjen: den blir en ny oppgave.
5. **Leietaker:** opprett et hjem av typen **Utleiebolig** som en tredje bruker, sett opp oppgaver og inviter en leietaker. Leietakeren skal verken se **Legg til oppgave** eller **Fjern oppgaven**.

Gjenta det som er relevant for PR-en du tester. README har egne trinn per story under «Kjøre appen lokalt», som kan følges på previewen så langt de ikke bruker seed-brukerne.

## 5. Gi tilbakemelding

- Skriv resultatet som en kommentar i PR-en: hva du testet, i hvilken nettleser, og hva som feilet. Legg ved feilmeldingen eller et skjermbilde.
- Feil som er funnet i KI-generert kode, føres også i [`docs/ki-logg/korrigeringer.md`](ki-logg/korrigeringer.md).
- Kjør `bmad-walkthrough` for PR-en hvis du vil ha en gjennomgang av hva du bør se på.

## Når noe ikke virker

| Symptom | Mulig årsak |
|---|---|
| «Noe gikk galt» ved registrering eller innlogging | Du er på en gammel preview. `<preview>/api/health/db` svarer da 503. Bruk adressen fra den åpne PR-en (punkt 1). |
| Vercel-bygget feiler | Migreringen feilet. Åpne byggeloggen. Migreringer må være bakoverkompatible med forrige versjon av koden. |
| `/api/health/db` feiler | Neon-grenen ble ikke laget (grensen på gratisplanen er 10 grener). Slett gamle grener i Neon. |
| Du blir kastet ut etter innlogging | Siden må kjøres på `https`. Åpne previewen via Vercel-adressen, ikke via en kopi av lenken med `http`. |
| Siden gir 404 på en dyp lenke | Skal ikke skje (SPA-rewrite i `vercel.json`). Meld fra i PR-en. |
| Alt ser tomt ut | Du er på en ny Neon-gren uten oppgaver. Gjør oppsettet i punkt 4. |
