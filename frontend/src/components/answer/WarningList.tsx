import type { WarningItem } from '../../api/generated-types';

interface WarningListProps {
  warnings: WarningItem[];
}

export function WarningList({ warnings }: WarningListProps) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <section className="warning-list" aria-label="Data quality warnings">
      {warnings.map((warning) => (
        <article className="warning-card" key={warning.code}>
          <strong>{warning.code.replaceAll('_', ' ')}</strong>
          <p>{warning.message}</p>
          {warning.record_ids && warning.record_ids.length > 0 ? (
            <small>Records: {warning.record_ids.join(', ')}</small>
          ) : null}
        </article>
      ))}
    </section>
  );
}
