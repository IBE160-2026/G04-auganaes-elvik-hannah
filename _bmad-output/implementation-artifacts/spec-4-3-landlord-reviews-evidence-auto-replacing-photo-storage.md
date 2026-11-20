---
title: 'Story 4.3: Landlord reviews evidence, auto-replacing photo storage'
type: 'feature'
created: '2026-11-20'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 073052a12f36767981d8137d00704f977f79225a
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-4-2-tenant-uploads-photo-evidence-with-immediate-auto-approval.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 4.2 stores a Tenant's photo but nothing shows it (FR-19). The Landlord cannot review it, and the Blob adapter from 4.2 was never run against the real SDK: it imports the *async* `put_blob`/`get_blob` and calls them without `await`, so on Vercel no photo is stored at all while the upload still answers 200.

**Approach:** Two Landlord-only routes on a Task: one answers whether current evidence exists (description and time, server-written), one streams the JPEG through the backend after `require_role` (AD-5, NFR5). Task Detail shows it to the Landlord. The Blob adapter moves to the SDK's synchronous API (`vercel.blob.sync`). The fixed key and the overwrite from 4.2 are kept and proven end to end.

**Decisions (Claude's choices under Eirik's mandate, 2026-11-20; Eirik reviews them in the PR):**
1. Only the Landlord of the Home views the photo. A Tenant, even the uploader, gets 403 and sees no photo or description (AC 4, NFR6). This settles the 4.2 deferred question.
2. Two routes, not a flag on `TaskOut`: `GET …/tasks/{task_id}/photo-evidence` answers 200 with `{evidence: null | {description, uploaded_at}}` (so «no photo yet» is never a 404, which keeps 404 meaning «no such Task»), and `GET …/photo-evidence/image` returns `image/jpeg`.
3. The image response sets `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`. No Blob URL, signed or not, reaches the browser.
4. The browser cannot put a Bearer token on `<img src>`, so it fetches the image through the API client as a blob and shows an object URL, revoked when the photo or the page changes. The query key includes `uploaded_at`, so a replaced photo is never shown stale. `alt` is the server's description; the browser formats no date.
5. A row without a stored object (or a store failure) is a Norwegian message, never a 500: 404 «Bildet finnes ikke lenger.» / 503.
6. An archived Task is 404 as everywhere (`is_active`), even though its photo is kept (PRD §5). A Task whose requirement was turned off still shows its last photo.
7. Nothing new is stored and no migration is needed: the row, key and overwrite are 4.2's.

## Boundaries & Constraints

**Always:** `require_role("landlord")` (the `Landlord` alias) runs first on both routes and `test_permissions.py` stays green. The key is computed from the Task id only. Task lookup is by Home and active Task. Norwegian UI text; the failure shows a retry.

**Never:** A Blob URL or signed URL to the browser, a photo history, a Tenant view, download or delete controls, browser date formatting, changing the upload path.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| View | Landlord, Task with evidence | info 200 with description and time; image 200 `image/jpeg`, the stored bytes, no-store header | N/A |
| No photo yet | Landlord, no row | info 200 `evidence: null`; image 404 | «Det finnes ikke noe bildebevis ennå.» |
| Row, object missing | Row but store returns None | image 404 | «Bildet finnes ikke lenger.» |
| Replaced | Second completion with a new photo | image returns the second bytes; one key, one row | N/A |
| Wrong role | Tenant or Household Member | 403 on both routes | `require_role` |
| Other Home | Landlord of another Home | 403 | `require_role` |
| Unknown / archived Task | Task id elsewhere or archived | 404 | `TASK_NOT_FOUND` |
| Store failure | `StorageError` on read | 503 | «Vi fikk ikke hentet bildet. Prøv igjen.» |
| Failure in browser | Network or 503 | Task Detail shows the message and «Prøv igjen» | Retry refetches |

</frozen-after-approval>

## Code Map

- `backend/app/domain/photo_evidence.py` -- add `current_evidence(session, membership, task_id)` and `read_photo(...)`; fix the docstring «Nothing here returns a photo». Reuse `evidence_key`, `tasks.TaskNotFound`, `StorageError`.
- `backend/app/routes/photo_evidence.py` -- the two GET routes with `Landlord`, `responses=` incl. `image/jpeg` so `schema.d.ts` types it.
- `backend/app/storage/blob.py` -- import from `vercel.blob.sync`; docstring.
- `backend/tests/test_photo_view.py` (new), `test_storage.py`, `test_permissions.py` -- the matrix; a test that the two Blob functions are not coroutine functions; permission test covers the new routes.
- `frontend/src/api/photoEvidence.ts`, `queries.ts` (`usePhotoEvidence`), `components/PhotoEvidenceView.tsx` (+ test, css), `routes/TaskDetail.tsx`, `test-utils/fakeApi.ts`, `schema.d.ts`.
- Docs: PRD FR-19 + Revision log, `epics.md` (4.2 AC «no route serves a photo»), AD-5 note, `README.md`, `deferred-work.md`, `docs/ki-logg/korrigeringer.md`.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/storage/blob.py`, `test_storage.py` -- synchronous SDK calls, guarded by a test
- [ ] `backend/app/domain/photo_evidence.py`, `routes/photo_evidence.py` -- the two routes; regenerate OpenAPI and `schema.d.ts`
- [ ] `backend/tests/test_photo_view.py`, `test_permissions.py` -- the matrix, each test names its line
- [ ] `frontend/...` -- the Landlord view on Task Detail, blob fetch with object URL, tests
- [ ] Docs above

**Acceptance Criteria:**
- Given a Tenant uploaded a photo, when the Landlord opens the Task, then they see the photo and its description.
- Given the task is completed again with a new photo, when the Landlord opens it, then only the new photo is shown and one object exists under `tasks/{task_id}/evidence.jpg`.
- Given any other user, when they request either route, then they get 403 and never a photo.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- CI runs the frontend. After merge to a Preview: upload as Tenant, view as Landlord against the real Blob store.
