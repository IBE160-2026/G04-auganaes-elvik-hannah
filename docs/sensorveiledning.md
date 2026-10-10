# Sensorveiledning – Del 1 (sammendrag)

Gruppens arbeidskopie av *Sensorveiledning IBE160 – Del 1: Applikasjon og prosess (70 %)*, høst 2026.
Vi bruker den som sjekkliste gjennom hele prosjektet. Ved tvil gjelder originalen fra faglærer.

Del 1 teller 70 % av karakteren, og refleksjonsrapporten (del 2) teller 30 %. Sensor kloner repoet ved fristen, følger README på en ren maskin, tester appen, leser historikken og prosessdokumentasjonen, kjører testene og stikkprøver koden.

## Kriterier og vekt

| Nr. | Kriterium | Vekt | Sensor ser etter |
|---|---|---|---|
| 1 | **Prosess og KI-styring** | 30 % | BMAD-dokumenter som er *brukt og oppdatert*, ikke generert én gang. Sporbarhet fra krav og stories til kode, og forklarte avvik. Jevn historikk med små commits og beskrivende meldinger. Branches, PR-er og issues. Lagrede prompts og KI-økter, med eksempler på at gruppen har presisert, avvist eller rettet KI-forslag. Begrunnede beslutninger. |
| 2 | **Funksjonalitet og omfang** | 20 % | Kjerneflytene fra proposal og README fungerer fra start til slutt. Omfanget passer til ambisjonen. Appen tåler feil input og gjentatte handlinger. Det som er utelatt eller endret, er begrunnet. |
| 3 | **Kvalitetssikring og testing** | 15 % | Automatiske tester av meningsfull logikk som kjøres via README. Manuelle testplaner der det er naturlig. Spor av kodegjennomgang og av feil i KI-kode som ble funnet og rettet. Validering, feilhåndtering og ingen hemmeligheter i koden. |
| 4 | **Design og brukeropplevelse** | 10 % | Konsistent visuelt uttrykk, tydelig navigasjon, gode tilbakemeldinger, feilmeldinger og tomtilstander. Grunnleggende universell utforming (kontrast, tastatur, alt-tekst, etiketter). Responsivt design. Spor av designarbeid. |
| 5 | **Kodekvalitet og arkitektur** | 10 % | Mappestrukturen samsvarer med arkitekturen. Lesbar kode med lite duplisering og død kode, og ingen utkommenterte KI-rester. Linter eller formatterer. Ryddig håndtering av konfigurasjon og avhengigheter. |
| 6 | **README og kjørbarhet** | 10 % | Hva appen er og hvem den er for. Forutsetninger med versjoner. Eksakte kommandoer for installasjon og oppstart. `.env.example`. Testdata og testbrukere, og hvordan testene kjøres. Mappeoversikt og lenker til prosessdokumentasjonen. Sensor bruker 15–20 minutter på å få appen til å kjøre. |
| 7 | **Ryddighet i repoet** | 5 % | Tydelig skille mellom kode og dokumentasjon. `.gitignore` for `node_modules`, `venv` og bygg. Ingen hemmeligheter i repoet eller historikken. Ingen løse testfiler eller gamle versjoner i roten. |

Karakter per kriterium regnes om til tall (A = 5 … F = 0) og vektes. Terskler: A ≥ 4,5 · B ≥ 3,5 · C ≥ 2,5 · D ≥ 1,5 · E ≥ 0,5.

## A–B-nivå for prosess (kriterium 1)

> Prosessen kan følges tydelig fra plan til ferdig app. Historikken viser jevn, iterativ utvikling. Prompts og beslutninger er dokumentert og koblet til konkrete endringer. Det finnes flere tydelige eksempler på at gruppen har vurdert, korrigert og styrt KI kritisk.

## Varseltegn sensor ser etter

- Nesten all kode lagt inn i én eller noen få commits rett før fristen.
- Planleggingsdokumenter som beskriver en annen app enn den som er levert, eller som tydelig er laget i etterkant.
- README som er en uendret mal, eller kommandoer som ikke virker.
- API-nøkler, passord eller `.env` som er committet. `node_modules`, `venv` eller build-mapper i repoet.
- Tester som feiler eller bare tester trivielle ting.
- Død kode, dupliserte filer eller rester fra forkastede KI-forsøk.
- Generell dokumentasjon av KI-bruk som ikke kan knyttes til konkrete endringer.

## Hvor vi dekker kriteriene

| Kriterium | Hvor sensor finner det |
|---|---|
| 1 Prosess | `_bmad-output/planning-artifacts/` (brief → PRD → UX → arkitektur → epics), [`docs/ki-logg/`](ki-logg/README.md), commit-historikk, PR-er |
| 3 Kvalitetssikring | review-filer i `_bmad-output/`, [`docs/ki-logg/korrigeringer.md`](ki-logg/korrigeringer.md), tester (kommer) |
| 4 Design | `_bmad-output/planning-artifacts/ux-designs/` (DESIGN.md, EXPERIENCE.md, mockups, tilgjengelighetsreview) |
| 6 README | [`README.md`](../README.md) |
