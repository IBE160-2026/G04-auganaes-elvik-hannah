// Story 2.1: the Må/Bør badge. The text is the meaning; the colour only reinforces it.
import { CLASSIFICATION_LABELS, type Classification } from '../api/tasks';
import './Badge.css';

export function Badge({ classification }: { classification: Classification }) {
  return <span className={`badge badge--${classification}`}>{CLASSIFICATION_LABELS[classification]}</span>;
}
