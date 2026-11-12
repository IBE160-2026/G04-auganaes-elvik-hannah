# Story 2.3: justere oppgaver

## 2026-11-11 kl. 20:19 — Eirik

### Oppgave
Merge statuspakken for 2.2 (PR #39) og bygge Story 2.3 med `bmad-build`: endre Må/Bør og hyppighet på oppgavedetaljer for husstandsmedlemmer og utleier, med låst visning for leietakere (issue #40). Deretter teste i Chrome og lage PR.

### Plan
- PR #39 merget (`2097492`), issue #40 laget, branchen `story/2-3-adjust-task` laget fra `main`.
- Epic 2-konteksten ble kompilert på nytt av en subagent, fordi `epics.md` var endret i 2.2.
- Specen ble skrevet etter en undersøkelse av koden og UX-dokumentene. Eirik svarte på to spørsmål:
  - **1b:** ny hyppighet flytter fristen fra samme startpunkt.
  - **2b:** endringer lagres med «Lagre endringer».
- Spec-review med én subagent ga 21 funn, og alle ble tatt inn. Eirik valgte å beholde hele specen (~1 950 tokens).
- En subagent implementerte. Tre reviewere ga 18 funn: 5 rettet, 9 avvist og 4 feil.
- Spec: [`spec-2-3-adjust-task-classification-frequency.md`](../../_bmad-output/implementation-artifacts/spec-2-3-adjust-task-classification-frequency.md).

### Resultat
- **Commits:**
  - `9a2070a`: spec, epic-kontekst og sprint-status `in-progress`
  - `f1cdf1d`: implementering, korrigeringer og sprint-status `review`
  - `75fd930`: resultatet fra Chrome-testen
  - Pushet. **PR #41** lukker #40.
- **Backend:**
  - `domain/tasks.adjust_task`, `can_adjust_tasks`/`ADJUST_ROLES` og `_open_instance`
  - `PATCH /api/homes/{home_id}/tasks/{task_id}`
  - `HomeOut.can_adjust_tasks`
  - Ingen migrering.
- **Frontend:**
  - Skjema på `TaskDetail`, der hvert felt er et utkast og bare endrede felt sendes. Ved feil vises «Prøv igjen».
  - Leietakere ser skrivebeskyttede felt med «Satt av utleier».
  - `useAdjustTask`
- **Dokumentasjon:**
  - README: avsnittet for 2.3, og setningen om 2.2 er rettet.
  - `epics.md`: merknad under 2.3.
  - Arkitekturen: revisjonsnotat om beslutning 1.
  - `deferred-work.md`: to oppføringer.
  - `korrigeringer.md`: fem rader.
- **Verifisering:**
  - 529 backendtester og 364 frontendtester passerer, og ruff, ESLint og build er rene.
  - Chrome-test mot `husly_smoke` (slettet etterpå):
    - Lagre uten endring gir «Ingen endringer å lagre.».
    - Må→Bør og «Hver 2. måned»: fristen flyttet seg 30 dager, og oppgaven står blant Bør i oversikten.
    - Med backenden stoppet vises feilen, og utkastet beholdes. Etter omstart lagrer «Prøv igjen».
    - Anders ser låste felt, og `PATCH` gir 403.
- **Hendelse:** implementasjonssubagenten mistet git-indeksen etter `git stash`/`pop` (en låsfil ble liggende igjen). Den bygde indeksen opp på nytt fra HEAD, og arbeidskopien ble ikke rørt. Jeg kontrollerte etterpå: ingen låsfil, ingen stash, og alle filene var der.
- **Lukket i issues.md:** merge av `chore/status-etter-story-2-2` og start på Story 2.3.

### Åpne punkter
- PR #41: CI på Linux og Windows, preview på Vercel (Eirik), `bmad-walkthrough`, og merge når Eirik sier fra.
- Etter merge av PR #41: 2-3 → done, CLAUDE.md (neste er Story 2.4) og en rad i KI-loggens README.
- Story 2.4 må endre `tasks_of` og `_open_instance` til tidligste *åpne* forekomst (`deferred-work.md`).

## 2026-11-11 kl. 20:57 — Eirik

### Oppgave
Fullføre PR #41: veiledning til preview-testen på Vercel, `bmad-walkthrough`, merge og statusarbeid etter merge.

### Plan
- Huke av CI i PR-en (grønn på Linux og Windows) og skrive en trinnvis veiledning for previewen, med en utleier og en leietaker via invitasjon.
- Walkthrough: orientering, løype i seks deler, risikopunkter og forslag til egne tester.
- Merge når Eirik godkjenner, og deretter en statusbranch fra `main`.

### Resultat
- **Preview:** Eirik testet på Vercel, og alt fungerte. Det er huket av i PR-en.
- **Walkthrough:** risikopunktene var:
  - at fristen flyttes i databasen (2.4 og 2.5 må endre `_open_instance`)
  - at låsen bare virker på Postgres
  - den nye skriveruten, der 403 kommer før 404
  - aliaset `ADJUST_ROLES = SETUP_ROLES`
  - at cachen oppdateres før lista hentes på nytt
- **Godkjenning:** Eirik godkjente uten å kjøre de valgfrie testene (to faner, låsen på Postgres, `/docs`).
- **Merge:** PR #41 er merget (`b30716c`), og issue #40 er lukket.
- **Statuscommit** `2311d0a` på `chore/status-etter-story-2-3`:
  - 2-3 → done
  - CLAUDE.md: neste er Story 2.4, med en merknad om `_open_instance` og en sjekk av git etter subagenter
  - rad i KI-loggens README

- **Klargjort for Story 2.4:**
  - PR #42 er merget (`fb4f199`).
  - Issue **#43** er laget.
  - Den lokale branchen `story/2-4-self-checkoff` er laget fra `main` (ikke pushet). Eirik kjører 2.4 i en ny terminal.

### Åpne punkter
- Story 2.4 med `bmad-build` i en ny økt, på branchen `story/2-4-self-checkoff` (issue #43). Øktfila `docs/ki-logg/okter/2026-11-11_eirik_2aa2818b.md` står som endret og committes sammen med 2.4-arbeidet.
- Valgfritt: teste låsen med to samtidige `PATCH` mot Postgres (ikke testet automatisk).
