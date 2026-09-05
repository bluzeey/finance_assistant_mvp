import { useQuery } from '@tanstack/react-query';

import { getMeta } from '../../api/client';

export function EvaluationPage() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: ({ signal }) => getMeta(signal) });
  const enabled = metaQuery.data?.features?.evaluation_enabled === true;

  return (
    <section className="page-section">
      <p className="eyebrow">Evaluation</p>
      <h2>Model benchmark evidence</h2>
      <div className="empty-card">
        <strong>Configured parser model</strong>
        <p>
          Provider: {metaQuery.data?.versions?.model_provider ?? 'unknown'} · Model:{' '}
          {metaQuery.data?.versions?.model_id ?? 'not loaded'}
        </p>
        <p>The model produces InterpretationDraft only; deterministic code computes official totals.</p>
      </div>
      {enabled ? (
        <p>Evaluation endpoints are enabled for this local/demo environment.</p>
      ) : (
        <div className="warning-card">
          <strong>Disabled outside demo mode.</strong>
          <p>No model accuracy, latency, or cost claims are shown until a benchmark run records evidence.</p>
        </div>
      )}
    </section>
  );
}
