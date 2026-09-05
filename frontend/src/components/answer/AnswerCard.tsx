import type { AnswerReceipt } from '../../api/generated-types';
import { formatInrFromDecimal } from '../../lib/money';
import { Button, ButtonLink } from '../ui/button';
import { InterpretationChips } from './InterpretationChips';
import { StatusBadge } from './StatusBadge';
import { WarningList } from './WarningList';

interface AnswerCardProps {
  receipt: AnswerReceipt;
  onViewEvidence?: () => void;
}

export function AnswerCard({ receipt, onViewEvidence }: AnswerCardProps) {
  const shouldShowPrimaryNumber = !['error', 'needs_clarification', 'not_answerable'].includes(
    receipt.status,
  );
  const primaryValue = receipt.primary_metric?.value ?? receipt.answer.value;

  return (
    <article className="answer-card" aria-labelledby={`answer-${receipt.query_id}`}>
      <div className="answer-card-header">
        <StatusBadge status={receipt.status} />
        <code title="Query ID">{receipt.query_id.slice(0, 8)}</code>
      </div>

      <h2 id={`answer-${receipt.query_id}`}>{receipt.answer.plain_language}</h2>

      {shouldShowPrimaryNumber && receipt.answer.currency === 'INR' ? (
        <p className="primary-metric" aria-label={`Primary metric ${formatInrFromDecimal(primaryValue)}`}>
          {formatInrFromDecimal(primaryValue)}
        </p>
      ) : null}

      <InterpretationChips receipt={receipt} />
      <WarningList warnings={receipt.warnings} />
      <BreakdownPreview receipt={receipt} />

      <footer className="answer-footer">
        <span>{receipt.lineage.source_row_count} source records</span>
        <span>Data through {receipt.lineage.data_as_of}</span>
        <span>{receipt.timings.total_ms} ms</span>
      </footer>

      <div className="answer-actions">
        <Button type="button" onClick={onViewEvidence}>
          View proof
        </Button>
        <ButtonLink href={receipt.exports.csv_url ?? '#'} aria-disabled={!receipt.exports.csv_url}>
          Export CSV
        </ButtonLink>
      </div>
    </article>
  );
}

function BreakdownPreview({ receipt }: { receipt: AnswerReceipt }) {
  if (receipt.breakdown.rows.length === 0) {
    return null;
  }

  const [firstColumn, secondColumn] = receipt.breakdown.columns;
  return (
    <table className="breakdown-table">
      <caption>Breakdown preview from the server receipt</caption>
      <thead>
        <tr>
          <th scope="col">{firstColumn?.label ?? 'Group'}</th>
          <th scope="col">{secondColumn?.label ?? 'Value'}</th>
        </tr>
      </thead>
      <tbody>
        {receipt.breakdown.rows.slice(0, 5).map((row) => {
          const label = String(row[firstColumn?.key ?? 'label'] ?? row.vendor ?? 'Group');
          const amount = row[secondColumn?.key ?? 'amount'];
          return (
            <tr key={`${label}-${String(amount)}`}>
              <td>{label}</td>
              <td className="numeric">{formatInrFromDecimal(amount)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
