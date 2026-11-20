---
title: 'Story 4.2: Tenant uploads Photo Evidence with immediate auto-approval'
type: 'feature'
created: '2026-11-19'
status: 'in-review'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: b84ad25709ebd7f769e3437f99903b3cc3a16b11
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-4-1-landlord-requires-photo-evidence-on-eligible-must-tasks.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 4.1 lets a Landlord require Photo Evidence on a Must task, but nothing stops a Tenant from ticking it without a photo, and a Tenant has no way to attach one (FR-18, FR-19). Photos need a private store that also works offline for sensors (FR-22, AD-15).

**Approach:** A Tenant uploads a photo from Task Detail; the server stores it under the fixed key `tasks/{task_id}/evidence.jpg` (private Vercel Blob when `BLOB_READ_WRITE_TOKEN` is set, a local folder otherwise), records one `photo_evidence` row per Task (AD-5) and completes the instance through the same `complete_task_instance` as the checkbox (AD-3). That function now refuses a Tenant's completion of a task that requires a photo unless a photo came with it. The upload is pessimistic: the task shows done only after the response.

**Decisions (Claude's choices under Eirik's mandate, 2026-11-19; Eirik reviews them in the PR):**
1. Only Tenants are blocked and only Tenants upload. FR-18 is about Tenants; a Landlord or Household Member completes a task as before.
2. The block lives inside `complete_task_instance` (a `photo_attached` flag the upload path sets), so no route can complete such a task for a Tenant without a photo. The plain route answers 409 with a Norwegian message.
3. JPEG only, at most 3.5 MB, checked by content and size on the server (Vercel's request body limit is 4.5 MB). The browser shrinks the picture to at most 1600 px as JPEG before sending and falls back to the original when it cannot.
4. The accessible description is written by the server («Bildebevis lastet opp av Martin, 29. sep», UTC date) and stored with the photo; the user never types it and no filename is used.
5. Storage is behind one interface with two adapters. The local folder (`PHOTO_STORAGE_DIR`, default `backend/.photo-evidence`, git-ignored) is what tests and local running use. The Blob adapter is written against Vercel's Python SDK but is only exercised once a store exists (Eirik and Claude create it in a separate step).
6. The photo is stored before the completion is committed; if the instance was already completed (someone else, a retry) nothing is stored and the current state is returned. A completion that then fails leaves the new photo under the key; it is replaced by the next upload. Accepted.
7. No route returns a photo in this story. Viewing is Story 4.3.

## Boundaries & Constraints

**Always:** Role checks server-side through `require_role`. The key is computed on the server from the task id, never from the request. The browser never gets a Blob URL. The photo is content-checked (JPEG signature) and size-capped before anything is stored. The upload goes through `complete_task_instance`, not a copy of it. All UI text Norwegian; the failure shows a retry at the control.

**Never:** A viewing route (4.3), a history of photos, a per-completion key, a pending or review state, a user-typed description, enforcement for the Landlord or Household Members, or touching the checkbox flow for tasks without a requirement.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Upload | Tenant, task requires photo, valid JPEG ≤ 3.5 MB | 200, task completed by the Tenant, next instance added, one `photo_evidence` row, file under the fixed key | N/A |
| Tick without photo | Tenant, plain complete route, task requires photo | 409, nothing completed | «Utleieren krever bilde. Last opp et bilde for å fullføre.» |
| Tick, no requirement | Tenant, task without requirement | Completes as before | N/A |
| Other roles | Landlord or Household Member completes a task that requires a photo | Completes as before | N/A |
| Wrong role | Household Member or Landlord calls the upload route | 403 | Same 403 as `require_role` |
| No requirement | Tenant uploads for a task that does not require a photo | 409, nothing stored | «Denne oppgaven krever ikke bilde.» |
| Not JPEG | PNG, text or empty file | 415, nothing stored or completed | «Bildet må være en JPEG-fil.» |
| Too large | Over 3.5 MB | 413, nothing stored or completed | «Bildet er for stort.» |
| Already done | Instance completed by someone else | 200 with the current state, nothing stored, first completer kept | N/A |
| Second completion | Next instance uploaded later | Same key overwritten, the one row updated to the new instance | N/A |
| Other Home / archived | Task id elsewhere | 404 | `TASK_NOT_FOUND` |
| Failure | Network or server error | The control shows an error and «Prøv igjen»; the task is not shown as done | Retry resends |

</frozen-after-approval>

## Code Map

- `backend/app/domain/tasks.py` -- `complete_task_instance` gets `photo_attached`; raises `PhotoRequired` for a Tenant on a task with `requires_photo_evidence`. 600 lines; new code goes in `photo_evidence.py`.
- `backend/app/domain/photo_evidence.py` -- `complete_with_photo`; description text; key function.
- `backend/app/models/photo_evidence.py` + new Alembic revision -- one row per Task (AD-5): task id (primary key), the instance that produced it, uploader, time, description.
- `backend/app/storage/` -- `PhotoStore` protocol, `LocalPhotoStore`, `BlobPhotoStore`, `get_photo_store()` chosen by `BLOB_READ_WRITE_TOKEN`; same shape as `app/push` and `app/ai`.
- `backend/app/routes/tasks.py`, `routes/photo_evidence.py` -- the plain complete route maps `PhotoRequired` to 409; the upload route.
- `backend/app/config.py`, `.env.example`, `README.md`, `.gitignore` -- `BLOB_READ_WRITE_TOKEN`, `PHOTO_STORAGE_DIR`.
- `frontend/src/routes/TaskDetail.tsx`, `TaskOverview.tsx`, `api/photoEvidence.ts`, `api/queries.ts`, `test-utils/fakeApi.ts` -- upload control on Task Detail; on Task Overview a Tenant's task that requires a photo shows «Last opp bilde» instead of a tickable checkbox.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/models/photo_evidence.py`, Alembic revision, `ci.yml` -- table with one row per Task
- [ ] `backend/app/storage/*`, `config.py`, `pyproject.toml` -- adapters and the Vercel SDK dependency
- [ ] `backend/app/domain/tasks.py`, `photo_evidence.py` -- the block and `complete_with_photo`
- [ ] `backend/app/routes/*`, `main.py` -- upload route, 409 on the plain route; regenerate OpenAPI and `schema.d.ts`
- [ ] `backend/tests/test_photo_upload.py`, `test_storage.py` -- the matrix, each test names its line
- [ ] `frontend/...` -- the upload control, Overview change, tests
- [ ] PRD FR-19 and Privacy Constraints (+ Revision log), `epics.md`, AD-5 note, README, `.env.example`, `deferred-work.md`

**Acceptance Criteria:**
- Given a task that requires a photo, when a Tenant ticks it without one, then the server refuses.
- Given a Tenant uploads a valid photo, when the response arrives, then the task is complete and no pending state was shown.
- Given the upload fails, when the Tenant sees it, then there is a retry and the task is not shown as done.
- Given no Blob token, when a photo is uploaded, then it lands under the fixed per-task key in the local folder.

## Implementation Notes

- Built directly by Claude under Eirik's mandate, 2026-11-19. Backend 874 tests green locally before the review fixes (882 after); frontend, `tsc`, eslint and the migration run only in CI. The Blob adapter is tested only with fakes.
- Review changed the order in `complete_with_photo`: Task row, requirement, instance row (locked, Postgres), then the photo check, the store and the evidence row, then `complete_task_instance`. A missing Task is a 404 whatever the body is.
- Review added: a streamed body read with a running size cap (`read_photo_body`), a plain `def` route, `StorageError` mapped to 503 «Vi fikk ikke lagret bildet.», a unique temporary file name in the local store, and `PhotoUpload` staying mounted after the answer so the result is announced.
- Without `BLOB_READ_WRITE_TOKEN` on Vercel the disk is read-only, so every upload answers 503 until the Blob store is connected. README says so.

## Spec Change Log

## Review Triage Log

Three reviewers (Blind Hunter, Edge Case Hunter, Verification Gap), 2026-11-19.

| Finding | Verdict | Evidence / route |
|---|---|---|
| The success text vanished: `TaskDetail` hid `PhotoUpload` as soon as the answer gave the task a completion (Blind, Edge) | high | patched: the component stays mounted and hides only the control; a test keeps the result visible |
| Two parallel uploads could both pass an unlocked check and overwrite the photo (Blind, Edge, Verification Gap) | medium | patched: Task and instance rows locked before the store (Postgres); the race itself is untested on SQLite and listed in deferred work |
| Body read in full before the size was known (no or false Content-Length) (Blind, Edge) | medium | patched: streamed with a running cap; chunked test added |
| `async def` route doing blocking database and storage work (Blind, Edge) | medium | patched: body read in an async dependency, route is a plain `def` |
| A failing store gave an unhandled 500 (Edge) | medium | patched: `StorageError` and a 503 with a Norwegian message; test added |
| Error order differed from the matrix: a bad body on a missing task gave 415 (Edge) | low | patched: Task and requirement are checked first; test added |
| Local temporary file name shared by parallel writes (Edge) | low | patched: unique name; cleanup on failure; two tests |
| Size check in `check_photo` untested (the route's header check hid it); «no route returns a photo» tested paths no route uses; «never ticks» test never clicked; vacuous assert (Verification Gap, Blind) | medium | patched: direct `check_photo` test, route enumeration, checkbox absence assertion, assert removed |
| `capture="environment"` hid the gallery on many phones (Blind) | low | patched: attribute removed |
| Refusal messages gave no next step; bitmap not closed on failure; stale upload box after a 409 (Blind, Edge) | low | patched |
| PRD-drift: §9 «only AI and push leave the system» was false with a photo store; upload for a task without requirement, retention after turning off or archiving, what the description holds (Blind, Edge, Verification Gap) | medium | patched: PRD, Revision log row |
| Photo stored before the commit, so a failed commit leaves a newer photo under the key (Blind, Edge, Verification Gap) | medium, known | accepted in the spec (decision 6), now stated in the AD-5 note and in deferred work |
| Description keeps the uploader's name and anonymisation would not remove it (Blind, Edge) | low | deferred |
| Only the JPEG signature is checked (Edge) | low | deferred |
| Description could overflow 200 characters if the name limit grows (Edge) | low | patched: cut at the column length |
| README bullet long; PRD «Landlord retrieves the photo» not yet met (Blind, Edge) | low | rejected as to structure; the Revision log row says retrieval is Story 4.3 |

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- CI runs the frontend and the migration; the Blob adapter is not exercised until a store exists.
