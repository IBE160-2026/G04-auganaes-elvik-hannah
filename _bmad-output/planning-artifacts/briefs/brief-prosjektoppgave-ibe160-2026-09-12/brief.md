---
title: "Product Brief: AI-Driven Household Task App"
status: ready
created: 2026-09-12
updated: 2026-10-11
---

> **Revision 2026-10-11:** Updated in response to the teacher's feedback of 2026-10-06 (`tilbakemelding-product-brief.md`): v1 is split into Trinn 1 and Trinn 2, success criteria are rewritten as testable criteria, the household is the primary user for Trinn 1, and local runnability is added to scope. See `sprint-change-proposal-2026-10-11.md`.

# Product Brief: AI-Driven Household Task App

## Executive Summary

Irregular household tasks — those with no fixed weekly rhythm, like deep-cleaning a bathroom or descaling a kettle — get forgotten, and forgetting them has real costs: mold, roommate irritation, and for landlords, expensive repairs and deposit disputes. This app gives any home a shared, always-current picture of what needs doing, split into non-negotiable "must" tasks and flexible "should" tasks, with app-recommended schedules, so nobody has to invent a reminder for a task they don't think about until it's already a problem.

It's built around one core mechanic — create a "home" and invite others into it — as a web app usable across phone, tablet, and PC. That mechanic works identically whether the "others" are a partner, roommates, or — for a landlord — tenants who inherit locked, must-do tasks they can't opt out of. An integrated AI assistant answers "how do I actually do this" questions in context, removing a different kind of friction than the gamification most chore apps rely on.

The product serves 4 segments with one shared foundation: single occupants and cohabiting couples (samboer) getting personal control over irregular tasks, kollektiv (roommate) households adding fairness and shared visibility on top, and landlords running a professional oversight tool that protects their properties and cuts maintenance surprises. No existing chore app models the landlord-tenant relationship — real, unaddressed white space.

Built by a 3-person team for IBE160, targeting a working, usable product by mid-December 2026.

## The Problem

Household chores split into two kinds: routine tasks people generally keep up with, and irregular, infrequent ones (deep-cleaning the bathroom, descaling, filter changes) that have no natural rhythm and are easy to forget. Left unaddressed, these small neglects compound.

In a kollektiv (a shared house with several roommates), a forgotten task like bathroom cleaning quickly becomes visible to everyone — it causes mold and odor, and breeds irritation between roommates. Over time this becomes a fairness problem: who did their part, who didn't, who's quietly resentful. This is grounded in the team's own lived experience of shared living, not formal user research.

In landlord-tenant situations, the same neglect has sharper financial teeth: undetected mold or wear leads to costly repairs, deposit disputes, and faster depreciation of the property. Landlords managing units at a distance have no reliable way to confirm maintenance-critical tasks are actually happening between inspections.

Today, people cope with tools that don't fit irregular tasks: text reminders, fridge notes, verbal nagging, shared lists. These work for daily or weekly routines but fail for infrequent tasks precisely because there's no fixed cadence to attach a reminder to — nobody thinks to write "clean behind the fridge" until it's already a problem.

The app treats kollektiv households and landlord-tenant relationships as two faces of one root cause — irregular tasks lacking rhythm and visibility — with different stakes on each side: trivsel (household contentment) and fairness for kollektiv households, cost control and asset protection for landlords. The same root problem exists even for someone living alone, minus the social and fairness dimension.

## The Solution

The app is built around a shared "home": someone creates it and invites others in — a roommate, a partner, or, for a landlord, a tenant. Everyone in a home sees the same overview of what needs doing, split into two tiers:

- **Must:** non-negotiable tasks. The app recommends which tasks should be "must" (for example, anything with a damage or health risk like mold), and household members can adjust this — except tenants, who see whatever their landlord has set as must and cannot override it.
- **Should:** everything else — desirable, but flexible.

For irregular tasks — the ones with no natural rhythm, and therefore the ones that get forgotten — the app proposes a recommended frequency (for example, "deep-clean the bathroom every 6 weeks"), which the user approves or adjusts. Landlords get the same kind of recommendation for their properties and can adjust it to their own judgment; tenants inherit whatever frequency the landlord sets and cannot change it.

Reminders and push notifications follow this schedule, alerting household members to upcoming or overdue tasks, and giving landlords a dedicated channel to push must-do tasks directly to their tenants.

When someone doesn't know *how* to do a task, an AI-powered bot helps in two ways: a quick "?" icon on any task gives an immediate, general answer (for example, "how do I clean grout"), with the option to escalate into a full conversation with the bot for follow-up questions.

## What Makes This Different

Existing chore apps (Sweepy, OurHome, Tody, Flatastic) are built for peer households — equals splitting equal work, motivated by points and leaderboards. None of them model a landlord-tenant relationship, where one party can assign non-negotiable tasks to another who can't opt out. This app's must/should permission hierarchy — landlord sets it, tenant inherits it — is a structural difference, not just a feature.

Rental platforms like Hybel.no solve the financial and legal side of renting (contracts, rent collection, tenant search) but stop there — physical property upkeep between tenant and landlord is untouched. This app is positioned to fill that gap, not compete with Hybel-style platforms, which could plausibly integrate with it down the line for a fuller landlord toolkit.

The other differentiator is the built-in AI assistant that answers "how do I do this" questions in context, addressing a gap competitors' point-based gamification doesn't touch: not knowing how to do the task at all.

Honestly: the moat here isn't proprietary technology — it's fit to an underserved segment (landlord-tenant and all household types in one tool) and thoughtful permission design, not a defensible technical edge. Execution and follow-through are what would actually differentiate this in practice.

## Who This Serves

**Household users — single, samboer, kollektiv**

Anyone living in a home, alone or with others, who wants a clear picture of what needs doing and when. The core mechanic is the same across all three — an overview of due and overdue tasks, with reminders for the irregular ones that otherwise get forgotten — but the social layer differs:

- **Single:** pure personal control. No fairness dimension — just "did I do this, and when's it due again."
- **Samboer / kollektiv:** control plus fair distribution. Who did what, avoiding the slow build-up of resentment from uneven effort.

Success for this group: fewer forgotten irregular tasks, less friction over who does what, a cleaner and better-maintained home.

**Landlords, and their tenants**

For the first release stage (Trinn 1) the primary user is the household — single, samboer and kollektiv — and design and the demo flow are built around them. The Landlord–Tenant role model (locked Must tasks and Frequency) is still part of Trinn 1, because it is the product's structural differentiator and its most testable rule set. The landlord is the one who creates a landlord home and invites tenants into it. The Landlord oversight tools (broadcast, notification cadence, Photo Evidence, portfolio dashboard) follow in Trinn 2. For landlords, this is closer to a professional oversight tool: visibility into whether maintenance-critical tasks are actually happening across units they don't visit often, plus the ability to push required tasks directly to tenants. Success here is cost reduction — catching neglect before it becomes a repair bill or a deposit dispute — and less time spent manually chasing tenants.

Tenants are the ones executing tasks, much like household members, but their task list includes landlord-assigned musts they don't get to deprioritize.

## Success Criteria

**Academic (this semester):** A usable, working product — not a mockup or pitch deck. Each criterion below is written so that it can become an automated test case.

*Trinn 1 (must be finished and stable):*
1. A Tenant cannot change a Must/Should classification or Frequency set by a Landlord; the server rejects the request (403).
2. Completing a task with Frequency N days schedules the next instance N days after the actual completion date, also when the task is completed late.
3. The task list always shows Must tasks before Should tasks.
4. When one Member completes a shared task, every Member of that Home sees it as complete, and the completion records who did it.
5. Only permitted roles can generate invite links; a Tenant's attempt is rejected, and an expired or used link shows a clear message.
6. A user with a Membership in one Home cannot read or change another Home's data.
7. The "?" quick answer shows an answer with a visible disclaimer, and works with mock answers when no API key is set.
8. A reviewer can run the app locally from the README using Docker, without the team's accounts or keys, and the automated tests pass.

*Trinn 2 (added once Trinn 1 is stable):*
- A Landlord broadcast reaches all Tenants of the targeted Home.
- The due-check never sends a duplicate notification for the same task instance and window.
- Photo Evidence cannot be required on task types that are not flagged eligible.
- The portfolio dashboard lists the Homes that have overdue Must tasks.

**Product (vision-level):** Real usage, positive reviews, fewer chore conflicts and fewer deposit disputes cannot be measured within the course. They are kept as long-term signals in the Vision section, not as success criteria for this semester.

## Scope

**Team:** 3 people. **Timeline:** now through mid-December 2026 (~13 weeks). **Stack:** Python backend, React (JavaScript) frontend.

v1 is delivered in two stages, so that a complete app exists even if Trinn 2 is not finished.

**Trinn 1 — minimal core flow (must be finished and stable first):**
- Create a "home" and invite members — supporting all 4 segments (single, samboer, kollektiv, landlord-tenant)
- Must/should task overview, with landlord-set tasks locked against tenant edits
- App-recommended frequency for irregular tasks, adjustable by the user or landlord (not by tenants), and automatic rescheduling after completion
- Self-checkoff with shared status and per-member attribution
- AI bot: contextual "?" quick-answer, with mock answers when no API key is set
- Responsive design across phone, tablet, and PC
- Local run: Docker-based local database, seed data, `.env.example` and a README, so a reviewer needs none of the team's accounts or keys

**Trinn 2 — added once Trinn 1 is stable:**
- Push notifications, including due/overdue, fairness-targeted reminders, a Landlord broadcast and Landlord-controlled cadence
- Photo Evidence for Landlord-required Must tasks
- Landlord portfolio dashboard
- AI chat for follow-up questions and the AI-generated onboarding guide

Photo Evidence and the portfolio dashboard were not in the original brief. They came in through the PRD user journeys (UJ-2, UJ-3) to realise the Landlord oversight value, and are placed in Trinn 2 because they are not needed for the core loop.

**Explicitly out of scope for v1:**
- Payment processing
- Actual Hybel.no (or similar platform) API integration — remains future vision
- Review/rating feature — currently a hypothesis for measuring product success, not a built feature

## Assumptions & Risks

- No confirmed partnership or integration agreement exists with Hybel.no or similar platforms — deeper integration is a stated future direction, not a validated one.
- The review/rating mechanism proposed as a product-success signal is a hypothesis for measurement, not yet a validated or built feature.
- This is a full scope for a 3-person, 13-week build. The AI bot and multi-role permission model are likely the highest-effort pieces. The Trinn 1 / Trinn 2 split is the mitigation: Trinn 1 is a complete app on its own.
- The app must be runnable by a reviewer without the team's accounts or keys. Trinn 1 therefore runs locally with Docker, seed data and mock modes for AI and push. Hosting (Vercel, Render, Supabase, cron-job.org) is an optional demo setup, not a requirement for running the app.

## Vision

In 2-3 years, this becomes the default way both sides of home-living stay on top of upkeep: private households (single, samboer, kollektiv) use it as a friction-free habit for shared living, while landlords and property managers rely on it as a serious oversight tool across multiple properties — cutting maintenance costs and tenant friction at scale.

Long-term signals of success, which cannot be measured within the course: users leaving positive reviews or ratings, fewer irregular tasks going overdue over time, repeat usage rather than abandonment, fewer chore-related conflicts in kollektiv households, and fewer maintenance surprises or deposit disputes for landlords.

Monetization runs on subscription, likely tiered between individual and household users and professional landlords managing several properties.

Further out, the product could integrate with rental platforms like Hybel.no to unify the financial and physical-upkeep sides of renting, and potentially broaden beyond cleaning into wider home management — maintenance scheduling, inventory, utilities. These remain open directions, not committed plans.
