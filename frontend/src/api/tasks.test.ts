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
    const thisYear = new Date(2026, 0, 1);

    expect(formatDueOn('2026-12-09', thisYear)).toBe('9. desember');
    // The pitfall it avoids: UTC midnight is still the 8th in Los Angeles.
    const naive = new Intl.DateTimeFormat('nb-NO', { day: 'numeric', month: 'long' });
    expect(naive.format(new Date('2026-12-09'))).toBe('8. desember');
  });

  it('shows the date as sent in a positive UTC offset', async () => {
    const { formatDueOn } = await loadIn('Europe/Oslo');
    expect(formatDueOn('2026-01-01', new Date(2026, 5, 1))).toBe('1. januar');
  });

  it('adds the year when it is not this year', async () => {
    const { formatDueOn } = await loadIn('Europe/Oslo');
    expect(formatDueOn('2027-01-03', new Date(2026, 10, 9))).toBe('3. januar 2027');
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
