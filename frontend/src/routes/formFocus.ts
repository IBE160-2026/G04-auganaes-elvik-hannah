import type { FieldErrors } from '../api/auth';

/** Moves focus to the first field (in form order) that has an error. */
export function focusFirstInvalid(form: HTMLFormElement | null, errors: FieldErrors): void {
  if (!form) return;
  for (const element of Array.from(form.elements)) {
    if (element instanceof HTMLInputElement && element.name in errors) {
      element.focus();
      return;
    }
  }
}
