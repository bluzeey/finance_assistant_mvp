import { useState } from 'react';

import { Button, ButtonLink } from '../ui/button';

import type { AnswerReceipt, ValidationCheck } from '../../api/generated-types';

interface EvidencePanelProps {
  receipt: AnswerReceipt;
}

const tabs = ['Receipt', 'Records', 'Checks', 'Query', 'Export'] as const;
type EvidenceTab = (typeof tabs)[number];

export function EvidencePanel({ receipt }: EvidencePanelProps) {
  const [activeTab, setActiveTab] = useState<EvidenceTab>('Receipt');

  return (
    <aside className="evidence-panel" aria-label="Answer evidence">
      <div className="tab-list" role="tablist" aria-label="Evidence tabs">
        {tabs.map((tab) => (
          <Button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            type="button"
            variant={activeTab === tab ? 'default' : 'outline'}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </Button>
        ))}
      </div>
      <div className="evidence-body" role="tabpanel">
        {activeTab === 'Receipt' ? <ReceiptTab receipt={receipt} /> : null}
        {activeTab === 'Records' ? <RecordsTab receipt={receipt} /> : null}
        {activeTab === 'Checks' ? <ChecksTab checks={receipt.validation.checks} /> : null}
        {activeTab === 'Query' ? <QueryTab receipt={receipt} /> : null}
        {activeTab === 'Export' ? <ExportTab receipt={receipt} /> : null}
      </div>
    </aside>
  );
}

function ReceiptTab({ receipt }: EvidencePanelProps) {
  return (
    <section>
      <h2>Receipt</h2>
      <dl className="receipt-list">
        <div><dt>Query ID</dt><dd><code>{receipt.query_id}</code></dd></div>
        <div><dt>Status</dt><dd>{receipt.status}</dd></div>
        <div><dt>Source rows</dt><dd>{receipt.lineage.source_row_count}</dd></div>
        <div><dt>Source hash</dt><dd><code>{receipt.lineage.source_record_ids_hash}</code></dd></div>
        <div><dt>Dataset</dt><dd>{receipt.lineage.dataset_version}</dd></div>
      </dl>
      <h3>How calculated</h3>
      <ol>
        {receipt.interpretation.human_readable_steps.map((step) => <li key={step}>{step}</li>)}
      </ol>
    </section>
  );
}

function RecordsTab({ receipt }: EvidencePanelProps) {
  return (
    <section>
      <h2>Records</h2>
      <p>{receipt.records_preview.total_count} records are attached to this immutable query.</p>
      {receipt.records_preview.rows.length === 0 ? (
        <p>The preview is empty in this scaffold; the backend records endpoint will fill it.</p>
      ) : null}
    </section>
  );
}

function ChecksTab({ checks }: { checks: ValidationCheck[] }) {
  return (
    <section>
      <h2>Validation checks</h2>
      <ul className="check-list">
        {checks.map((check) => (
          <li key={check.check_id} data-status={check.status}>
            <strong>{check.label}</strong>
            <span>{check.status}</span>
            <p>{check.details}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function QueryTab({ receipt }: EvidencePanelProps) {
  return (
    <section>
      <h2>Query plan</h2>
      <p>Named query: {receipt.lineage.executed_query_name ?? 'none'}</p>
      <pre>{JSON.stringify(receipt.interpretation.canonical_query_plan, null, 2)}</pre>
    </section>
  );
}

function ExportTab({ receipt }: EvidencePanelProps) {
  return (
    <section>
      <h2>Export</h2>
      <p>Exports must match {receipt.lineage.source_row_count} rows and hash <code>{receipt.lineage.source_record_ids_hash}</code>.</p>
      <div className="button-row">
        <ButtonLink href={receipt.exports.csv_url ?? '#'} aria-disabled={!receipt.exports.csv_url}>
          CSV
        </ButtonLink>
        <ButtonLink href={receipt.exports.xlsx_url ?? '#'} aria-disabled={!receipt.exports.xlsx_url}>
          Excel
        </ButtonLink>
      </div>
    </section>
  );
}
