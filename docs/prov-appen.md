# Prøv funksjonene i appen

Oppskrifter for å prøve hver funksjon i Husly lokalt, én per story. Appen må kjøre først (se [«Kjøre appen lokalt» i README](../README.md#kjøre-appen-lokalt)), og du bruker eksempelbrukerne derfra (`mari@example.com`, `jonas@example.com`, `kari@example.com` og `anders@example.com`, alle med passordet `husly-demo`). Mange av oppskriftene lager eller sletter data og forutsetter en nyseedet database; det står i begynnelsen av hver.

## Prøv regelen for å opprette hjem (Story 1.9)

Stegene forutsetter en nyseedet database (`uv run python -m app.seed` fra `backend/` på en tom database), siden de lager nye hjem.

1. Logg inn som Kari, gå til **Innstillinger** og trykk **Opprett nytt hjem**. Hun er bare utleier, så hun får velge både **Husstand** og **Utleiebolig**. Velg **Husstand**, gi hjemmet et navn og trykk **Opprett hjem**. Hun blir husstandsmedlem i det nye hjemmet og kommer til **Sett opp oppgaver**.
2. Logg inn som Jonas, gå til **Innstillinger** og trykk **Opprett nytt hjem**. Siden heter **Opprett ny utleiebolig**, tilbyr bare utleiebolig og sier at medlemskapet hans i «Mari og Jonas sitt hjem» ikke endres. Etter at han har opprettet den, er han både husstandsmedlem der og utleier i den nye.
3. Serveren håndhever regelen selv om noen prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `jonas@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Kjør `POST /api/homes` med `{"name": "Hytta", "type": "household"}`. Svaret er 409 med «Du er allerede med i «Mari og Jonas sitt hjem». Du kan bare være med i ett hjem om gangen.», og ingenting blir lagret.
4. Jonas og Kari har nå to hjem hver, og bytter mellom dem under **Dine hjem** (se «Prøv oppgaveoversikten» under).

## Prøv invitasjon (Story 1.4)


1. Logg inn som Mari og velg **Medlemmer og invitasjon** øverst på oppgaveoversikten. Under **Medlemmer** ser hun seg selv («(deg)») og Jonas som husstandsmedlemmer. Trykk **Lag invitasjonslenke**. Lenken kan brukes én gang og gjelder i 7 dager; **Lag ny lenke** lager en til, og de gamle virker fortsatt.
2. Åpne lenken i et privat vindu. Du ser hjemmet og rollen. Velg **Opprett konto og bli med** og lag en ny bruker. Du er da med i «Mari og Jonas sitt hjem» som husstandsmedlem.
3. Logg ut (private vinduer i samme nettleser deler innlogging), eller bruk en annen nettleser, og åpne den samme lenken igjen. Nå står det at lenken ikke lenger er gyldig.
4. Logg inn som Anders (leietaker) og åpne **Medlemmer og invitasjon** for «Storgata 12». Under **Medlemmer** ser han Kari Hansen (Utleier) og seg selv (Leietaker, «(deg)»), men ingen knapp for å invitere (Story 1.5). Serveren nekter også, hvis han prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `anders@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Kjør `GET /api/homes` og kopier `id` til «Storgata 12».
   4. Kjør `POST /api/homes/{home_id}/invites` med den `id`-en. Svaret er 403.
   5. Logg inn som Mari på samme måte og kjør `GET /api/homes/{home_id}/members` med `id`-en til «Storgata 12». Svaret er 403, fordi hun ikke er medlem der (Story 1.5).
5. Er du allerede husstandsmedlem eller leietaker i ett hjem, kan du ikke bli med i et annet; invitasjonssiden sier fra om det. Utleierroller teller ikke, så en utleier kan i tillegg bli med i ett slikt hjem. Det er den samme regelen som avgjør om du kan opprette en husstand (Story 1.9).

## Prøv å forlate et hjem (Story 1.8)


1. Logg inn som Jonas og åpne **Medlemmer og invitasjon**. Trykk **Forlat hjemmet**. Teksten forklarer hva som skjer; ingenting er sendt ennå, og **Avbryt** tar deg tilbake. Trykk **Ja, forlat hjemmet**. Du havner på **Opprett hjemmet ditt** med beskjeden «Du har forlatt «Mari og Jonas sitt hjem».», og kan opprette et eget hjem eller bli med via en ny invitasjon.
2. Logg inn som Mari og åpne **Medlemmer og invitasjon**. Under **Medlemmer** står bare hun. Hun har ingen **Fjern**-knapp: et husstandsmedlem kan bare forlate selv.
3. Logg inn som Anders i én nettleser og åpne **Medlemmer og invitasjon** for «Storgata 12». Logg inn som Kari i en annen nettleser (eller et privat vindu), åpne samme side og trykk **Fjern** ved Anders og så **Ja, fjern Anders Johnsen**. Kari ser «Anders Johnsen er fjernet.». Bytt så til en annen fane i Anders sin nettleser (eller minimer vinduet) og tilbake, uten å laste siden på nytt: han blir sendt til **Opprett hjemmet ditt**, uten feilside. Det holder ikke å klikke mellom to vinduer som står side om side; appen henter data på nytt når fanen blir synlig igjen, ikke når vinduet får fokus. Kari har ingen **Forlat hjemmet**-knapp: en utleier kan ikke forlate sin egen utleiebolig.
4. Angre ved å kjøre `uv run python -m app.seed` fra `backend/` igjen. Den legger Jonas tilbake i «Mari og Jonas sitt hjem» og Anders tilbake i «Storgata 12» (med en ny invitasjonslenke), og sletter ingenting. Har Jonas eller Anders laget eller blitt med i et annet hjem i mellomtiden, hopper seed-en over dem.

## Prøv oppgaveoppsett (Story 2.1)


1. Lag en ny bruker og opprett et hjem (steg 3 og 4 under «Første innlogging» i [README](../README.md#4-første-innlogging)). Du havner på **Sett opp oppgaver** med åtte anbefalte oppgaver, hver med **Ta med**, **Må**/**Bør** og **Hvor ofte**.
2. Gjør «Vask stekeovnen» til **Må** og velg **Hver 2. måned**, og fjern haken ved «Rens sluket». Trykk **Lagre oppgavene**. Du havner på oppgaveoversikten for hjemmet, som viser sju oppgaver med «Vask stekeovnen» blant Må-oppgavene og uten «Rens sluket». Tilbake-knappen i nettleseren tar deg ikke til skjemaet igjen.
3. Fjerner du alle hakene og trykker **Lagre oppgavene**, står det «Velg minst én oppgave.», og ingenting blir sendt.
4. Oppsettet kjøres én gang per hjem. Åpner du `/hjem/<id>/oppgaveoppsett` igjen etterpå, blir du sendt til oppgaveoversikten for hjemmet. Lagrer du i to faner, svarer serveren 409 på den andre, og den fanen går også dit.
5. Logg inn som Anders (leietaker). Han ser oppgavene Kari har satt opp for «Storgata 12», men kan ikke sette opp oppgaver selv; serveren svarer 403 på `POST /api/homes/{home_id}/tasks/setup` (prøv i <http://localhost:8000/docs> som i invitasjonseksempelet). En utleier som oppretter en ny utleiebolig, setter opp oppgavene med en gang, før noen leietaker er med; har et eldre hjem ingen oppgaver, står **Sett opp oppgaver** ved det under **Dine hjem** på **Innstillinger**.

## Prøv oppgaveoversikten (Story 2.2)

Steg 3 og 4 forutsetter en nyseedet database, siden de lager et nytt hjem.

1. Logg inn som Mari. `/` åpner oppgaveoversikten for hjemmet hennes. Alle **Må**-oppgaver står over alle **Bør**-oppgaver, også når en Bør-oppgave er forfalt. Mens seed-dataene er ferske, står «Rens sluket» (Må) med «Snart forfall» i gult og fet skrift, og «Støvsug og vask gulvene» (Bør) med «Forfalt — frist var …» i rødt. Antall dager («i dag», «i morgen», «om N dager») og hvilke oppgaver som er forfalt, flytter seg med datoen, siden oppgavene er satt opp relativt til dagen seed-en ble kjørt. «Snart forfall» betyr innen 3 dager, og det er serveren som avgjør det (`due_status` i `GET /api/homes/{home_id}/tasks`).
2. Trykk på en oppgave for å se detaljene. Der kan du endre **Må**/**Bør** og **Hvor ofte** (se Story 2.3 under). Trykk **Oppdater** øverst (eller dra lista ned på mobil) for å hente oppgavene på nytt; skjermleseren sier «Oppdatert». Bruk Tab: fokus går fra overskriften via **Medlemmer og invitasjon**, **Legg til oppgave** (for husstandsmedlemmer og utleiere, se Story 2.6 under) og **Oppdater** gjennom oppgavene ovenfra og ned (først avkrysningsboksen, så selve oppgaven, se Story 2.4 under), og til slutt fanelinja. **Husly** øverst er en lenke til `/`.
3. Logg inn som Kari, gå til **Innstillinger**, trykk **Opprett nytt hjem**, velg **Husstand** og sett opp oppgavene. Hun har nå to hjem, og oppgaveoversikten viser **Bytt hjem**.
4. Trykk **Bytt hjem** og velg «Storgata 12» under **Dine hjem**. Last siden på nytt og gå til `/` (eller trykk **Husly**): appen åpner «Storgata 12», fordi det er sist brukte hjem. Dette huskes i nettleseren (`localStorage`), per bruker og per enhet, ikke på serveren.

## Prøv å justere oppgaver (Story 2.3)

Forutsetter en nyseedet database, siden stegene endrer oppgavene.

1. Logg inn som Mari, trykk på «Rens sluket» og velg **Bør**. Ingenting lagres før du trykker **Lagre endringer**; da står det «Lagret». Trykker du uten å ha endret noe, står det «Ingen endringer å lagre.», og ingenting blir sendt.
2. Logg inn som Jonas i en annen nettleser (eller et privat vindu) og trykk **Oppdater** på oppgaveoversikten: «Rens sluket» står nå blant Bør-oppgavene.
3. Velg en ny verdi under **Hvor ofte** og lagre. Fristen flytter seg fra samme startpunkt: «Hver måned» → «Hver 2. måned» gir 30 dager senere frist. Velger du et kortere intervall, kan oppgaven bli forfalt med en gang. Endrer du bare Må/Bør, står fristen stille.
4. Logg inn som Anders (leietaker) og åpne en oppgave i «Storgata 12». **Viktighet** og **Hvor ofte** vises låst med «Satt av utleier», og kan nås med Tab, men ikke endres. Serveren svarer også 403 for ham, uansett innhold, hvis han prøver direkte i <http://localhost:8000/docs>:
   1. Kjør `POST /api/auth/login` med `anders@example.com` og `husly-demo`, og kopier `access_token` fra svaret.
   2. Trykk **Authorize** øverst og lim inn tokenet.
   3. Hent id-en til «Storgata 12» med `GET /api/homes` og en oppgave-id med `GET /api/homes/{home_id}/tasks`.
   4. Kjør `PATCH /api/homes/{home_id}/tasks/{task_id}` med for eksempel `{"classification": "should"}`. Svaret er 403.
5. Går du fra siden uten å lagre, forkastes endringen uten advarsel.

## Prøv å krysse av oppgaver (Story 2.4)

Forutsetter en nyseedet database, siden stegene endrer oppgavene. Med Story 2.4 er også Story 2.5 (ny frist etter avkrysning) bygget.

1. Logg inn som Mari. «Avkalk vannkokeren» er allerede krysset av, med «Fullført … av Jonas» i grønt og overstreket navn: seed-en lar Jonas krysse den av to dager før seed-en ble kjørt.
2. Logg inn som Jonas i en annen nettleser (eller et privat vindu) og kryss av «Støvsug og vask gulvene». Boksen blir krysset av med en gang, uten bekreftelse, og kortet viser «Fullført i dag». Ditt eget navn står aldri der. Neste frist regnes fra dagen du krysset av (UTC) pluss hyppigheten, også når oppgaven var forfalt: «Hver 2. uke» gir frist om 14 dager. Også «i dag» og «i går» i notatet regnes i UTC-døgn, så en avkrysning like etter midnatt norsk tid kan stå som «Fullført i går».
3. Trykk **Oppdater** hos Mari: kortet viser «Fullført i dag av Jonas». Kortet står som fullført så lenge neste frist er mer enn 3 dager unna; når den nærmer seg, kommer fristen og en tom boks tilbake.
4. En avkrysset boks kan ikke angres. Den forblir krysset av, og et nytt trykk sender ingenting. Med Tab kommer du først til boksen («Merk «X» som fullført») og så til oppgaven.
5. Slå av nettet (i Chrome: DevTools → **Network** → **Offline**) og kryss av en oppgave hos Jonas. Kortet viser «Fullført i dag». Slå nettet på igjen: avkrysningen blir sendt av seg selv, uten at kortet hopper tilbake. **Begrensning:** avkrysninger som er gjort uten nett, ligger bare i minnet. Laster du siden på nytt eller lukker appen før nettet er tilbake, går de tapt, og du må krysse av på nytt.
6. Logg inn som Jonas, åpne **Medlemmer og invitasjon** og trykk **Forlat hjemmet**. Hos Mari står det nå «Fullført i dag av tidligere medlem»; avkrysningen blir stående.
7. Anders (leietaker) kan også krysse av oppgaver i «Storgata 12». Bildebevis kommer i Epic 4.

## Prøv å legge til og fjerne oppgaver (Story 2.6)

Forutsetter en nyseedet database, siden stegene endrer oppgavene.

1. Logg inn som Mari og trykk **Legg til oppgave** øverst på oppgaveoversikten. Lista viser katalogoppgavene hjemmet mangler, og **Egen oppgave** nederst. Ingenting er valgt på forhånd; trykker du **Legg til** uten å velge, står det «Velg en oppgave.».
2. Velg en katalogoppgave: anbefalt **Må**/**Bør** og **Hvor ofte** står ferdig valgt, og du kan endre dem. Lagre: oversikten viser «La til «X».» (leses opp av skjermleseren, vises bare én gang), og oppgaven står i lista med første frist i dag pluss hyppigheten.
3. Velg **Egen oppgave**: fokus går til navnefeltet. Navnet trimmes og må være 1–100 tegn. Et navn som en aktiv oppgave allerede har (også med andre store og små bokstaver, og også katalogoppgavenes navn), avvises med en melding ved feltet. Egne oppgaver kan aldri kreve bildebevis (Epic 4).
4. Åpne en oppgave og trykk **Fjern oppgaven**. Bekreftelsen kommer inline: «Oppgaven forsvinner fra lista for alle i hjemmet. Det som er gjort, blir stående.» Trykk **Ja, fjern oppgaven**: du kommer til oversikten med «Fjernet «X».», og oppgaven er borte for alle (trykk **Oppdater** hos Jonas). **Avbryt** sender ingenting. Oppgaven slettes ikke; den arkiveres, og det som er gjort, blir stående i databasen.
5. Legg til den samme katalogoppgaven igjen: den blir en ny oppgave med ny første frist. Fjerner du alle oppgavene, står det «Ingen oppgaver i hjemmet ennå.» med **Legg til oppgave**; oppsettet av oppgaver tilbys ikke på nytt.
6. Logg inn som Anders (leietaker): han ser verken **Legg til oppgave** eller **Fjern oppgaven**, og serveren svarer 403 på `POST /api/homes/{home_id}/tasks` og `DELETE /api/homes/{home_id}/tasks/{task_id}` (prøv i <http://localhost:8000/docs> som i Story 2.3). Før oppgavene er satt opp, svarer serveren 409 «Sett opp oppgavene først.» på en `POST`.

## Prøv porteføljen (Story 6.1, FR-20)

Forutsetter en nyseedet database, siden stegene lager et nytt hjem. Seed-dataene gir Kari bare ett utleiehjem, og porteføljen finnes først når en utleier har to.

1. Logg inn som Kari: fanelinja har ingen **Portefølje**, siden hun bare har «Storgata 12», og `GET /api/portfolio` svarer 403 (prøv i <http://localhost:8000/docs>).
2. Gå til **Innstillinger**, trykk **Opprett nytt hjem**, velg **Utleiebolig** og sett opp oppgavene. Nå står **Portefølje** i fanelinja.
3. Åpne den: «Storgata 12» står øverst som **Forsinket**, siden seed-dataene har forfalte Må-oppgaver mens de er ferske, og det nye hjemmet står som **Alt i orden**. Et hjem uten oppgaver står som **Ikke satt opp**. Statusen avgjøres på serveren (`backend/app/domain/portfolio.py`) og er alltid en tekst, ikke bare en farge.
4. På mobil (under 600 px) er hver rad en lenke til **Administrer hjemmet**. På nettbrett og desktop velger du en rad og får forfalte Må-oppgaver i kolonnen ved siden av. **Oppdater** (eller et trekk ned fra toppen på mobil) henter statusen på nytt.

## Prøv å slette konto (Story 1.10, FR-25)

Forutsetter en nyseedet database, siden stegene sletter en bruker.

1. Logg inn som Jonas og kryss av en oppgave, for eksempel «Vask badet grundig» (seed-dataene har ingen avkrysninger fra ham, så uten dette er det ingenting som kan bli «Tidligere medlem»). Gå så til **Innstillinger** og bla ned til **Slett konto**. Trykk den: teksten sier at det ikke kan angres, og at det du har gjort i andres hjem blir stående som «Tidligere medlem». Trykk **Ja, slett kontoen** uten passord: «Skriv inn passordet ditt for å bekrefte.» Med feil passord: «Passordet stemmer ikke.»
2. Skriv `husly-demo` og trykk **Ja, slett kontoen**. Du blir sendt til innloggingen, og `jonas@example.com` kan ikke logge inn igjen. Logg inn som Mari: i «Mari og Jonas sitt hjem» står oppgaven Jonas krysset av nå med «Fullført i dag av tidligere medlem».
3. Logg inn som Kari (utleier, med «Storgata 12» som eneste utleiehjem) og prøv **Slett konto**: serveren svarer 409 «Du må fjerne leietakerne før du kan slette kontoen. Gjelder: Storgata 12.», så lenge Anders er leietaker. Fjern Anders under **Medlemmer og invitasjon**, og slett kontoen: «Storgata 12» slettes med oppgavene og bildene sine.
4. Reglene står i `backend/app/domain/account_deletion.py` og testene i `backend/tests/test_account_deletion.py`. Brukerraden slettes aldri: den anonymiseres (`users.deleted_at`), så historikken henger sammen. Seed lager bare eksempelbrukerne på nytt der de mangler (en slettet bruker blir en ny Jonas som blir med i hjemmet igjen), ikke de slettede hjemmene eller historikken; kjør seed på en tom database for å få alt tilbake.

Innloggingen fungerer også i Safari på `http://localhost`, fordi cookien bare får `Secure` på Vercel (eller med `AUTH_COOKIE_SECURE=true`).
