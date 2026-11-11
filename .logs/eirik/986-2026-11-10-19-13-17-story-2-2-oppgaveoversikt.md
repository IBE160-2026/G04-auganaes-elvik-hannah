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
