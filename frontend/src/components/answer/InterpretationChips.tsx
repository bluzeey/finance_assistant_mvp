import type { AnswerReceipt } from '../../api/generated-types';

interface InterpretationChipsProps {
  receipt: AnswerReceipt;
}

export function InterpretationChips({ receipt }: InterpretationChipsProps) {
  const plan = receipt.interpretation.canonical_query_plan;
  const dateRange = getObject(plan?.date_range);
  const filters = getObject(plan?.filters);

  const chips = [
    ['Metric', receipt.primary_metric?.label ?? 'No metric'],
    ['Period', formatPeriod(dateRange)],
    ['Date field', valueLabel(dateRange?.date_field)],
    ['Status', valueLabel(filters?.payout_status ?? filters?.transaction_status ?? filters?.reconciliation_status)],
    ['Currency', receipt.answer.currency ?? 'None'],
  ];

  return (
    <dl className="interpretation-chips" aria-label="Interpreted query">
      {chips.map(([label, value]) => (
        <div className="chip-pair" key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function getObject(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function formatPeriod(dateRange: Record<string, unknown> | null): string {
  if (!dateRange) {
    return 'Not set';
  }
  const start = String(dateRange.start ?? '');
  const endExclusive = String(dateRange.end_exclusive ?? '');
  if (!start || !endExclusive) {
    return 'Not set';
  }
  return `${start} to before ${endExclusive}`;
}

function valueLabel(value: unknown): string {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (typeof value === 'string') {
    return value.replaceAll('_', ' ');
  }
  return 'All';
}
