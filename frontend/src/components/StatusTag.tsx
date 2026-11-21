// Story 6.1: the Portfolio's status tag (DESIGN.md: status tags are pills). The text is the
// meaning; the colour only reinforces it.
import { STATUS_LABELS, type PortfolioStatus } from '../api/portfolio';
import './StatusTag.css';

export function StatusTag({ status }: { status: PortfolioStatus }) {
  return <span className={`status-tag status-tag--${status}`}>{STATUS_LABELS[status]}</span>;
}
