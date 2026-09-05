import { useQuery } from '@tanstack/react-query';

import { getDataHealth } from '../../api/client';

const statusLabels = {
  pass: 'Pass',
  warning: 'Warning',
  fail: 'Fail',
} as const;

export function DataHealthPage() {
  const healthQuery = useQuery({
    queryKey: ['data-health'],
    queryFn: ({ signal }) => getDataHealth(signal),
  });

  if (healthQuery.isLoading) {
    return (
      <section className="page-section" aria-busy="true">
        <p className="eyebrow">Data health</p>
        <h2>Checking freshness, coverage, integrity, and quality</h2>
        <div className="empty-card">Loading backend data-health checks…</div>
      </section>
    );
  }

  if (healthQuery.isError || !healthQuery.data) {
    return (
      <section className="page-section">
        <p className="eyebrow">Data health</p>
        <h2>Data-health checks unavailable</h2>
        <div className="warning-card" role="alert">
          The finance service could not verify data-health checks. No financial number is shown.
        </div>
      </section>
    );
  }

  const data = healthQuery.data;
  return (
    <section className="page-section">
      <p className="eyebrow">Data health</p>
      <h2>Freshness, coverage, integrity, and quality checks</h2>
      <div className="hero-card">
        <strong>Overall state: {data.overall_state}</strong>
        <p>Data as of {data.data_as_of}. Warnings explain whether answers remain verified or qualified.</p>
      </div>
      <div className="health-check-list">
        {data.checks.map((check) => (
          <article className="empty-card" key={check.check_id}>
            <div className="answer-card-header">
              <h3>{check.label}</h3>
              <span className={`status-badge ${statusClass(check.status)}`}>
                <span aria-hidden="true">●</span>
                {statusLabels[check.status]}
              </span>
            </div>
            <p>{check.details}</p>
            <small>
              {check.category} · affected records: {check.affected_record_count}
            </small>
            {check.sample_record_ids && check.sample_record_ids.length > 0 ? (
              <p>
                Samples:{' '}
                {check.sample_record_ids.map((id) => (
                  <code key={id}>{id} </code>
                ))}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function statusClass(status: 'pass' | 'warning' | 'fail'): string {
  if (status === 'pass') {
    return 'status-verified';
  }
  if (status === 'warning') {
    return 'status-qualified';
  }
  return 'status-error';
}
