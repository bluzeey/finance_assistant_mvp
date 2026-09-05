import type { MetaResponse } from '../../api/generated-types';

interface DatasetFreshnessChipProps {
  meta?: MetaResponse;
  isLoading?: boolean;
  isError?: boolean;
}

export function DatasetFreshnessChip({ meta, isLoading, isError }: DatasetFreshnessChipProps) {
  if (isLoading) {
    return <span className="chip chip-muted">Checking data…</span>;
  }

  if (isError || !meta) {
    return <span className="chip chip-warning">Data status unknown</span>;
  }

  const label = meta.dataset.freshness_state === 'fresh' ? 'Fresh' : 'Review';
  return (
    <span className="chip chip-data" aria-label={`Dataset ${label}. Data through ${meta.dataset.data_as_of}`}>
      {label}: data through {formatDisplayDate(meta.dataset.data_as_of)}
    </span>
  );
}

function formatDisplayDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-');
  return `${Number(day)} ${monthName(Number(month))} ${year}`;
}

function monthName(month: number): string {
  return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][
    month - 1
  ];
}
