// Story 5.3 (FR-16, UX-DR onboarding card): the guide for a new Tenant. As a card it sits at the
// top of the Task Overview with «Skjul»; as a page (Settings → Velkomstguide) it has no button.
// It names the Home, shows the introduction, lists the Home's current Must tasks with their
// frequencies in words, and carries the AI disclaimer when an AI wrote the introduction.
import type { Ref } from 'react';
import { GUIDE_MESSAGES, type Guide } from '../api/onboarding';
import { FREQUENCY_LABELS, type Frequency } from '../api/tasks';
import './OnboardingGuide.css';

type Props = {
  guide: Guide;
  /** Set for the card: shows «Skjul». */
  onDismiss?: () => void;
  dismissFailed?: boolean;
  dismissing?: boolean;
  /** The card's heading is level 2 (the page has its own h1); the page uses the given level. */
  headingLevel?: 1 | 2;
  /** The page focuses its heading on arrival, as every page does. */
  titleRef?: Ref<HTMLHeadingElement>;
};

export function OnboardingGuide({ guide, onDismiss, dismissFailed, dismissing, headingLevel = 2, titleRef }: Props) {
  const Heading = headingLevel === 1 ? 'h1' : 'h2';
  // The subtitle sits one level below the title, so the outline never skips a level.
  const Subheading = headingLevel === 1 ? 'h2' : 'h3';
  return (
    <section className="onboarding-guide" aria-labelledby="onboarding-guide-title">
      <Heading
        id="onboarding-guide-title"
        ref={titleRef}
        tabIndex={titleRef ? -1 : undefined}
        className="onboarding-guide__title"
      >
        {GUIDE_MESSAGES.heading(guide.home_name)}
      </Heading>
      <p className="onboarding-guide__intro">{guide.intro}</p>
      <Subheading className="onboarding-guide__subtitle">{GUIDE_MESSAGES.mustHeading}</Subheading>
      {guide.must_tasks.length === 0 ? (
        <p className="onboarding-guide__meta">{GUIDE_MESSAGES.noMust}</p>
      ) : (
        <ul className="onboarding-guide__tasks">
          {guide.must_tasks.map((task) => (
            <li key={task.name}>
              <span className="onboarding-guide__task">{task.name}</span>{' '}
              <span className="onboarding-guide__meta">{frequencyText(task.frequency_days)}</span>
            </li>
          ))}
        </ul>
      )}
      {guide.disclaimer && <p className="onboarding-guide__disclaimer">{guide.disclaimer}</p>}
      {guide.demo && <p className="onboarding-guide__meta">{GUIDE_MESSAGES.demo}</p>}
      {onDismiss && (
        <div className="onboarding-guide__actions">
          <button type="button" className="onboarding-guide__button" disabled={dismissing} onClick={onDismiss}>
            {GUIDE_MESSAGES.dismiss}
          </button>
          <p className="onboarding-guide__meta">{GUIDE_MESSAGES.readAgain}</p>
        </div>
      )}
      {dismissFailed && (
        <p className="onboarding-guide__error" role="alert">
          {GUIDE_MESSAGES.dismissFailed}
        </p>
      )}
    </section>
  );
}

function frequencyText(days: number): string {
  return FREQUENCY_LABELS[days as Frequency] ?? `Hver ${days}. dag`;
}
