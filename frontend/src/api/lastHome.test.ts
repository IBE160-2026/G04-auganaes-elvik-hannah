// Story 2.2 (decisions 3 and 12): which Home "/" opens, and storage that may throw.
import type { Home } from './homes';
import { OLA, OLAS_HOME, homesResponse } from '../test-utils/fakeApi';
import { lastHomeKey, pickHome, readLastHome, recordLastHome } from './lastHome';

const A: Home = { ...OLAS_HOME, id: '00000000-0000-4000-8000-0000000000a1', name: 'A' };
const B: Home = { ...OLAS_HOME, id: '00000000-0000-4000-8000-0000000000b1', name: 'B', type: 'landlord', role: 'landlord' };
const C: Home = { ...B, id: '00000000-0000-4000-8000-0000000000b2', name: 'C' };

afterEach(() => vi.restoreAllMocks());

describe('pickHome', () => {
  it('picks the stored Home while it is still listed', () => {
    expect(pickHome(homesResponse([A, B, C], [], A.id), C.id)).toBe(C);
  });

  it('falls back to lived_in_home_id when the stored Home is gone', () => {
    expect(pickHome(homesResponse([B, A], [], A.id), 'gone')).toBe(A);
  });

  it('falls back to the first Home when nothing is stored and the user lives in none', () => {
    expect(pickHome(homesResponse([C, B], [], null), null)).toBe(C);
  });

  it('falls back to the first Home when lived_in_home_id is not in the list', () => {
    expect(pickHome(homesResponse([C, B], [], 'stale'), 'gone')).toBe(C);
  });

  it('picks nothing from an empty list', () => {
    expect(pickHome(homesResponse([], ['household']), A.id)).toBeUndefined();
  });
});

describe('the stored Home', () => {
  it('is kept per user', () => {
    recordLastHome(OLA.id, B.id);
    recordLastHome('someone-else', C.id);

    expect(readLastHome(OLA.id)).toBe(B.id);
    expect(readLastHome('someone-else')).toBe(C.id);
    expect(localStorage.getItem(lastHomeKey(OLA.id))).toBe(B.id);
  });

  it('is nothing without a user', () => {
    recordLastHome(undefined, B.id);
    expect(localStorage.length).toBe(0);
    expect(readLastHome(undefined)).toBeNull();
  });

  it('survives storage that throws: nothing stored, nothing read', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('QuotaExceededError');
    });
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('SecurityError');
    });

    expect(() => recordLastHome(OLA.id, B.id)).not.toThrow();
    expect(readLastHome(OLA.id)).toBeNull();
    expect(pickHome(homesResponse([B, A], [], A.id), readLastHome(OLA.id))).toBe(A);
  });
});
