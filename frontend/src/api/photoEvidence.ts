// Story 4.1 (FR-18, AD-6): the Landlord's Photo Evidence requirement on one Task, with Norwegian copy.
import { api } from './client';
import { toApiError } from './errors';
import type { Task } from './tasks';

export const PHOTO_EVIDENCE_MESSAGES = {
  failed: 'Vi fikk ikke lagret kravet om bilde. Prøv igjen.',
} as const;

// Story 4.2 (FR-19): the Tenant's upload. 409, 413 and 415 carry the server's Norwegian reason.
export const PHOTO_UPLOAD_MESSAGES = {
  failed: 'Vi fikk ikke lastet opp bildet. Prøv igjen.',
  uploading: 'Laster opp …',
  done: 'Bilde lastet opp. Oppgaven er fullført.',
} as const;

// The browser shrinks a photo before sending: a phone picture is often over the server's limit.
// Same cap as backend/app/domain/photo_evidence.py in spirit; the server still checks the size.
const MAX_EDGE = 1600;
const JPEG_QUALITY = 0.8;

/**
 * The picture as a JPEG of at most 1600 px on its long side. Falls back to the file as it came
 * when the browser cannot decode or draw it (the server then accepts or refuses it as it is).
 */
export async function prepareImage(file: Blob): Promise<Blob> {
  try {
    if (typeof createImageBitmap !== 'function') return file;
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, MAX_EDGE / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext('2d');
    if (!context) return file;
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    const jpeg = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
    return jpeg ?? file;
  } catch {
    return file;
  }
}

/**
 * Completes the Tenant's open instance with the photo as the request body (AD-3, AD-11). The
 * answer is the Task as it is after the completion. A 403 is the global handler's.
 */
export async function uploadPhotoEvidence(homeId: string, task: Pick<Task, 'id' | 'instance_id'>, photo: Blob): Promise<Task> {
  const { data, error, response } = await api.POST(
    '/api/homes/{home_id}/tasks/{task_id}/instances/{instance_id}/photo-evidence',
    {
      params: { path: { home_id: homeId, task_id: task.id, instance_id: task.instance_id } },
      // The body is the JPEG itself, not JSON: the schema types it as a string.
      body: photo as unknown as string,
      bodySerializer: (body) => body as unknown as BodyInit,
      headers: { 'Content-Type': 'image/jpeg' },
    },
  );
  if (!data) {
    throw toApiError(response, error, { passThrough: [409, 413, 415], fallback: PHOTO_UPLOAD_MESSAGES.failed });
  }
  return data;
}

/** A 409 carries the server's Norwegian reason (not eligible, not a Må task); else the fallback. */
export async function setPhotoEvidenceRequirement(
  homeId: string,
  taskId: string,
  required: boolean,
): Promise<boolean> {
  const { data, error, response } = await api.PUT(
    '/api/homes/{home_id}/tasks/{task_id}/photo-evidence-requirement',
    { params: { path: { home_id: homeId, task_id: taskId } }, body: { required } },
  );
  if (!data) {
    throw toApiError(response, error, { passThrough: [409], fallback: PHOTO_EVIDENCE_MESSAGES.failed });
  }
  return data.requires_photo_evidence;
}
