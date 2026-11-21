---
title: "Sprint Change Proposal: account deletion with anonymisation"
date: 2026-11-21
status: approved
trigger: "The PRD (§5 Non-Goals) says account deletion is not built and that the team aims to add it; the Epic 3, 4 and 6 reviews left four deferred items that wait for it (`deferred-work.md`). All planned stories are done and there is time."
scope: moderate
rollback: none needed (plan change only; no code reverted)
---

# Sprint Change Proposal — 2026-11-21

## 1. Issue summary

**Trigger.** PRD §5 says «Account deletion is not built in this course version; the team aims to add it. The user row would be anonymised; the Landlord case is undecided, because FR-3 requires exactly one Landlord and FR-23 forbids a Landlord leaving.» All 24 stories are done (Story 6.1, PR #87), the team has two to three weeks left, and the privacy constraints in §9 (account data, what other Members see) read stronger with a way to remove the data.

**Evidence.**
- `deferred-work.md`: «Decide `ON DELETE` behaviour for `push_subscriptions` and `due_notifications` when account deletion (PRD §5) is built» (Story 3.2) and «Scrub or derive the uploader's name in the saved description» (Story 4.2).
- The tables that point at `users.id`: `memberships`, `invite_links` (`created_by_user_id`, `used_by_user_id`), `push_subscriptions`, `due_notifications`, `ai_usage`, `photo_evidence` (uploader), `task_instances` (`completed_by_user_id`), and `fairness_nudges`. The text of `photo_evidence.description` also holds the uploader's name.
- AD-16 already shows history by a former Member as «Tidligere medlem» (`domain/photo_evidence.shown_description`, `domain/tasks`).

**Type.** A requirement the team announced, not a defect.

## 2. Decisions (Eirik, 2026-11-21)

1. **A Landlord must remove the Tenants first.** Deletion is refused (409) while any of the user's Landlord Homes has a Tenant, with the message to remove them first (FR-23). Landlord Homes without Tenants are deleted with the account. No change to FR-3 or FR-23.
2. **Everything else as proposed.** The user row is **anonymised, not deleted**: name becomes «Tidligere medlem», the e-mail is replaced by an unusable address, the password hash is cleared and `deleted_at` is set. The user's Memberships, push devices, claimed notifications, AI counts, fairness records and unused invite links are deleted. Homes left without any Member are deleted with their photos. History in other Members' Homes stays as «Tidligere medlem».

**Decided by Claude (not a choice the user would notice).**
- **No `ON DELETE` is needed.** Because the user row is kept, no foreign key to `users` is ever violated; the domain function deletes the dependent rows explicitly, in one transaction. This settles the Story 3.2 deferred item.
- **A signed-in request after deletion is refused.** `current_user` and the refresh route answer 401 for a row with `deleted_at` set, so an access or refresh token issued earlier stops working.
- **Password confirmation.** The request carries the password, so a stolen session cannot delete the account.
- **The uploader's name in `photo_evidence.description`** is rewritten to «Tidligere medlem» for the user's evidence in Homes that remain.
- **Photos** in deleted Homes are removed from the store (`PhotoStore.delete`), local or Blob.
- **Stage:** Trinn 1 (privacy of the account). It is built after Story 6.1 and is the last item in the plan.

## 3. Impact analysis

**Epics.** Epic 1 gets Story 1.10. No other epic changes.

**PRD.** FR-25 added (4.1, after FR-23); §5 Non-Goals drops the account deletion bullet; FR-23's «nothing is deleted» consequence says the deletion in FR-25 is the one exception; the Privacy Constraints list account deletion; FR-1 to FR-24 becomes FR-1 to FR-25; one row in the Revision log.

**Architecture.** AD-17 added after AD-16: anonymise, never delete the user row; explicit deletes in one domain function; `deleted_at`; refusal rule for Landlords with Tenants. `ARCHITECTURE-SPINE.md` is otherwise unchanged.

**Code (Story 1.10).** One Alembic migration (`users.deleted_at`), `domain/accounts.delete_account`, `PhotoStore.delete` (local and Blob), `DELETE /api/me`, a «Slett konto» section under Settings with a confirmation and the password, tests, README. Tests cover every dependent table, the Landlord refusal, a refused token, and that nothing of another user changes.

**Deferred items settled.** `ON DELETE` for push and due notifications (no `ON DELETE`: explicit delete), the uploader's name in the photo description (rewritten).

## 4. Recommended approach

**Direct adjustment:** one new story in Epic 1, built on `story/1-10-kontosletting` with its own issue and PR. No existing story is reopened.

**Effort and risk.** About one day. The risk is a missed table: the test lists every table with a foreign key to `users` or `homes` from the metadata and asserts that none keeps a row for the deleted user, so a future table fails the test until it is handled.

## 5. Detailed change proposals

| Artifact | Section | Change |
|---|---|---|
| `prd.md` | §4.1 | New FR-25 with testable consequences |
| `prd.md` | FR-23 | The «nothing is deleted» line points to FR-25 |
| `prd.md` | §5 Non-Goals | Remove the account deletion bullet |
| `prd.md` | §9 Privacy | Account deletion states what is deleted and what stays |
| `prd.md` | Revision log | One row linking this proposal |
| `epics.md` | FR list, FR map, Stage line | FR-25, Epic 1 (Story 1.10), Trinn 1 |
| `epics.md` | Epic 1 | Story 1.10 with acceptance criteria |
| `ARCHITECTURE-SPINE.md` | AD-17 | New decision |
| `sprint-status.yaml` | Epic 1 | `1-10-account-deletion: backlog` |

## 6. Implementation handoff

**Scope: moderate.** Direct implementation by the developer agent, with the PRD and epics updated in the same session as this proposal (done) and the spec written at story start (re-read the ACs against this proposal first, action A3). Success: Story 1.10 merged with green CI, the deferred items marked with an outcome, README describing how to try it.
