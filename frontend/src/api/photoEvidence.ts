// Story 4.1 (FR-18, AD-6): the Landlord's Photo Evidence requirement on one Task, with Norwegian copy.
import { api } from './client';
import { toApiError } from './errors';

export const PHOTO_EVIDENCE_MESSAGES = {
  failed: 'Vi fikk ikke lagret kravet om bilde. Prøv igjen.',
} as const;

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
