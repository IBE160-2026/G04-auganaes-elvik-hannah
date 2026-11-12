// Story 2.1: due dates are calendar dates, shown as sent whatever the viewer's time zone.
const ORIGINAL_TZ = process.env.TZ;

afterEach(() => {
  process.env.TZ = ORIGINAL_TZ;
  vi.resetModules();
});

/** The module as loaded in this time zone (its date formats are built on load). */
async function loadIn(timeZone: string) {
  process.env.TZ = timeZone;
  vi.resetModules();
  return import('./tasks');
}

describe('formatDueOn', () => {
  it('shows the date as sent in a negative UTC offset, where new Date(iso) is the day before', async () => {
    const { formatDueOn } = await loadIn('America/Los_Angeles');

    expect(formatDueOn('2026-12-09', 2026)).toBe('9. desember');
    // The pitfall it avoids: UTC midnight is still the 8th in Los Angeles.
    const naive = new Intl.DateTimeFormat('nb-NO', { day: 'numeric', month: 'long' });
    expect(naive.format(new Date('2026-12-09'))).toBe('8. desember');
  });

  it('shows the date as sent in a positive UTC offset', async () => {
    const { formatDueOn } = await loadIn('Europe/Oslo');
    expect(formatDueOn('2026-01-01', 2026)).toBe('1. januar');
  });

  it('adds the year when it is not this year', async () => {
    const { formatDueOn } = await loadIn('Europe/Oslo');
    expect(formatDueOn('2027-01-03', 2026)).toBe('3. januar 2027');
  });
});

describe('labels', () => {
  it('has a Norwegian label for every interval and both classes', async () => {
    const { CLASSIFICATION_LABELS, FREQUENCY_LABELS } = await import('./tasks');
    expect(CLASSIFICATION_LABELS).toEqual({ must: 'Må', should: 'Bør' });
    expect(Object.keys(FREQUENCY_LABELS).map(Number)).toEqual([7, 14, 30, 42, 60, 90, 182, 365]);
    expect(FREQUENCY_LABELS[182]).toBe('Hvert halvår');
  });
});

// Story 2.2 (decision 8): the due text follows the server's status and day count.
describe('dueText', () => {
  it.each([
    [-1, 'overdue', '2026-11-09', 'Forfalt — frist var 9. november'],
    [0, 'due_soon', '2026-11-10', 'Snart forfall — i dag'],
    [1, 'due_soon', '2026-11-11', 'Snart forfall — i morgen'],
    [3, 'due_soon', '2026-11-13', 'Snart forfall — om 3 dager'],
    [4, 'later', '2026-11-14', 'Neste gang: 14. november'],
  ] as const)('%i days: %s', async (days, status, dueOn, text) => {
    const { dueText } = await loadIn('Europe/Oslo');
    expect(dueText({ due_on: dueOn, due_status: status, days_until_due: days })).toBe(text);
  });

  it('takes the day word from days_until_due, not from the browser date', async () => {
    const { dueText } = await loadIn('Pacific/Kiritimati');
    // The browser may already be on the 11th; the word follows the server's day count.
    expect(dueText({ due_on: '2026-11-10', due_status: 'due_soon', days_until_due: 0 })).toBe(
      'Snart forfall — i dag',
    );
  });

  it('takes the year from the server day count near New Year, whatever the browser year is', async () => {
    const { dueText } = await loadIn('Europe/Oslo');
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2031, 0, 1));
    try {
      // The server's today is 2026-12-30, so a due date in January is next year.
      expect(dueText({ due_on: '2027-01-03', due_status: 'later', days_until_due: 4 })).toBe(
        'Neste gang: 3. januar 2027',
      );
      // The server's today is 2026-12-27, so 31 December is this year.
      expect(dueText({ due_on: '2026-12-31', due_status: 'later', days_until_due: 4 })).toBe(
        'Neste gang: 31. desember',
      );
    } finally {
      vi.useRealTimers();
    }
  });
});

// Story 2.4 (decision 4): the completion note, from the server's fields only.
describe('completionText', () => {
  const base = { completed_on: '2026-11-03', days_since: 0, completed_this_year: true, by: 'you', name: null } as const;

  it.each([
    ['today, own', { ...base, completed_on: '2026-11-10' }, 'Fullført i dag'],
    ['yesterday, own', { ...base, days_since: 1 }, 'Fullført i går'],
    ['a date this year', { ...base, days_since: 7 }, 'Fullført 3. november'],
    ['a date last year', { ...base, completed_on: '2025-12-31', days_since: 2, completed_this_year: false }, 'Fullført 31. desember 2025'],
    ['another Member', { ...base, by: 'member', name: 'Jonas' }, 'Fullført i dag av Jonas'],
    ['a former Member', { ...base, days_since: 1, by: 'former_member' }, 'Fullført i går av tidligere medlem'],
  ] as const)('%s', async (_, completion, text) => {
    const { completionText } = await loadIn('Europe/Oslo');
    expect(completionText(completion)).toBe(text);
  });

  it('never names the viewer, even if a name is sent', async () => {
    const { completionText } = await loadIn('Europe/Oslo');
    expect(completionText({ ...base, name: 'Sara' })).toBe('Fullført i dag');
  });

  it('shows the completion date as sent west of Greenwich, and never reads the browser clock', async () => {
    const { completionText } = await loadIn('America/Los_Angeles');
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2031, 0, 1));
    try {
      expect(completionText({ ...base, days_since: 8 })).toBe('Fullført 3. november');
    } finally {
      vi.useRealTimers();
    }
  });
});

describe('labels for the checkbox', () => {
  it('names the action and the Task', async () => {
    const { checkboxLabel, completedLabel } = await import('./tasks');
    expect(checkboxLabel('Rens sluket')).toBe('Merk «Rens sluket» som fullført');
    expect(completedLabel('Rens sluket')).toBe('«Rens sluket» er fullført');
  });
});
