export function ReconciliationPage() {
  return (
    <section className="page-section">
      <p className="eyebrow">Reconciliation</p>
      <h2>Open, partial, and disputed items</h2>
      <p>
        This page will distinguish transaction amount, reconciled amount, and remaining open amount from
        backend aggregates. Partial items must use unreconciled_amount only.
      </p>
      <div className="kpi-grid" aria-label="Reconciliation KPI placeholders">
        <div className="kpi-card"><span>Open amount</span><strong>Server-owned</strong></div>
        <div className="kpi-card"><span>Partial</span><strong>Server-owned</strong></div>
        <div className="kpi-card"><span>Disputed</span><strong>Server-owned</strong></div>
      </div>
    </section>
  );
}
