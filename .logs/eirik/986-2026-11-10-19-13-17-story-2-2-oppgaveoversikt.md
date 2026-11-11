# Story 2.2: oppgaveoversikt

## 2026-11-10 kl. 19:13 — Eirik

### Oppgave
Fortsette arbeidet: bygge Story 2.2 (issue #37) med `bmad-build`. Storyen gjelder oppgaveoversikten med Må først, fanelinja, bytte mellom hjem («Dine hjem», `/hjem/<id>`, `/` = sist brukte hjem) og at Husly-logoen lenker til `/`.

### Plan
- Kompilere Epic 2-konteksten på nytt, siden `epics.md` var endret 10.11.
- Sjekke om storyen burde deles. Teamet valgte å beholde alt i én story.
- Skrive spec-en og få sju åpne spørsmål besvart. Teamet valgte alle anbefalingene.
- Spec-review med én subagent ga 18 funn, og alle ble tatt inn som beslutning 8–14.
- Implementering med en subagent.
- Kodegjennomgang med tre reviewere: 31 funn, hvorav 10 rettet.
- Spec: [`spec-2-2-must-first-task-overview.md`](../../_bmad-output/implementation-artifacts/spec-2-2-must-first-task-overview.md).

### Resultat
- **Commits:** `789db44` (spec, epic-kontekst og KI-logg) og `9d9298a` (implementering). Branchen `story/2-2-task-overview` er pushet, og **PR #38** lukker #37.
- **Backend:**
  - `domain/tasks.due_status` med `DUE_SOON_DAYS = 3`.
  - `TaskOut.due_status` og `days_until_due`, begge regnet ut fra samme UTC-dato.
- **Frontend:**
  - `TaskOverview` (`/hjem/<id>`)
  - `TaskDetail`, som bare viser informasjon
  - `Settings` (`/innstillinger`, med «Dine hjem» og «Logg ut»)
  - `TabBar`, og Husly-logoen som lenke til `/`
  - `lastHome.ts`, som husker sist brukte hjem i localStorage
  - «Logg ut» på Opprett hjem
  - invitasjon og oppgaveoppsett går til `/hjem/<id>`
- **Planendringer i `epics.md`:**
  - Merkelappene heter Må/Bør.
  - Kriteriet om avkrysningsboks og fokusrekkefølge er flyttet til 2.4.
  - Portefølje-fanen er flyttet til 6.1.
- **Dokumentasjon:** README har fått «Prøv oppgaveoversikten». `korrigeringer.md` har fått fem nye rader.
- **Verifisering:** 487 backendtester og 352 frontendtester passerer, og ruff, ESLint og build er rene. Kort test i Chrome mot en engangsdatabase (`husly_smoke22`, slettet etterpå).
- **Status:** sprint-status for 2-2 er `review`, og spec-en er `done`.
- **Lukket i issues.md:** utloggingsknapp på Opprett hjem, AC om bytte mellom hjem og AC om logolenken.

### Åpne punkter
- PR #38: sjekke CI på Linux og Windows.
- PR #38, manuelle tester:
  - 320 px bredde
  - Kari oppretter et hjem nummer to og bytter mellom dem
  - godta en invitasjon når man allerede har et hjem
  - forlate det hjemmet man sist brukte
- PR #38: preview på Vercel (Eirik), `bmad-walkthrough`, og deretter merge på Eiriks ord.
- Etter merge: statuscommit med 2-2 → done, CLAUDE.md (neste er Story 2.3) og en rad i KI-loggens README.

## 2026-11-11 kl. 19:33 — Eirik

### Oppgave
Fortsette med PR #38 (Story 2.2): sjekke CI, kjøre de manuelle testene, få Eiriks preview-test, ta `bmad-walkthrough` og merge, og deretter gjøre statusarbeidet etter merge.

### Plan
- Sjekke CI på PR #38.
- Manuelle tester i Chrome mot engangsdatabasen `husly_smoke` (backend :8001, Vite :5174 med midlertidig config, slettet etterpå).
- Forklare preview-testene for Eirik. Han testet selv på Vercel.
- `bmad-walkthrough` (orientering, gjennomgang, detaljer, testing), så kjøre testene fra walkthroughen og merge etter Eiriks «gjør testene og merge etterpå».
- Statusbranch `chore/status-etter-story-2-2` fra `main`.

### Resultat
- **CI:** grønn på Linux og Windows.
- **Manuelle tester, alle bestått:**
  - 320 px, via en iframe fordi vinduet ikke lot seg krympe
  - Kari oppretter hjem nummer to og bytter
  - forlate sist brukte hjem: meldingen vises én gang
  - godta en invitasjon med et hjem fra før
- Resultatene er ført inn i spec-en og PR-sjekklista (`f7f12ae`).
- **Preview på Vercel:** Eirik testet, og alt fungerte.
- **Walkthrough:** detaljgjennomgangen pekte på:
  - UTC-dato for «i dag»
  - at 2.4 må endre «neste forfall» til tidligste åpne forekomst
  - klientvakten (tilgangen håndheves av `require_role`)
  - at id-er i `localStorage` blir liggende etter utlogging
  - den globale `overscroll-behavior`
- **Testene fra walkthroughen**, lagt som kommentar på PR #38:
  - farger: gul og rød, fet skrift
  - tastaturrekkefølge og «Oppdatert»
  - API-felter (`due_status`, `days_until_due`)
  - feil ved lasting: lista blir stående, og meldingen leses opp
  - Min forventning om «Prøv igjen» etter omlasting med API-et nede var feil. Da kommer innloggingssiden, fordi økta ikke kan gjenopprettes (Story 1.2). Dette er ikke en feil i 2.2.
- **Merge:** PR #38 er merget (`cab0ccb`), og issue #37 er lukket.
- **Statuscommit** `d00b562` på `chore/status-etter-story-2-2`:
  - 2-2 → done i sprint-status
  - CLAUDE.md: neste er Story 2.3
  - rad i KI-loggens README
  - øktfilene i KI-loggen

### Åpne punkter
- Vurdere om «i dag» i `due_status` skal være norsk dato i stedet for UTC. Mellom kl. 00 og 01/02 norsk tid ligger statusen én dag bak.
- Merge statusbranchen `chore/status-etter-story-2-2`, og deretter Story 2.3 med `bmad-build`.
