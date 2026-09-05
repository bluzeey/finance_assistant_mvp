import { describe, expect, it } from 'vitest';

import { formatInrFromDecimal } from './money';

describe('formatInrFromDecimal', () => {
  it('uses Indian grouping without changing the canonical value', () => {
    expect(formatInrFromDecimal('10000874.04')).toBe('₹1,00,00,874.04');
  });

  it('keeps negative values clearly signed', () => {
    expect(formatInrFromDecimal('-380000.00')).toBe('−₹3,80,000.00');
  });

  it('does not invent a value for invalid input', () => {
    expect(formatInrFromDecimal(null)).toBe('—');
    expect(formatInrFromDecimal('not-money')).toBe('—');
  });
});
