export function formatInrFromDecimal(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  const raw = typeof value === 'number' ? value.toFixed(2) : String(value);
  const match = raw.match(/^(-?)(\d+)(?:\.(\d{1,2}))?$/);
  if (!match) {
    return '—';
  }

  const [, negative, integerPart, fraction = '00'] = match;
  const grouped = groupIndianDigits(integerPart);
  const paddedFraction = fraction.padEnd(2, '0');
  return `${negative ? '−' : ''}₹${grouped}.${paddedFraction}`;
}

function groupIndianDigits(integerPart: string): string {
  if (integerPart.length <= 3) {
    return integerPart;
  }

  const lastThree = integerPart.slice(-3);
  const leading = integerPart.slice(0, -3);
  const groups: string[] = [];
  for (let index = leading.length; index > 0; index -= 2) {
    groups.unshift(leading.slice(Math.max(0, index - 2), index));
  }
  return `${groups.join(',')},${lastThree}`;
}
