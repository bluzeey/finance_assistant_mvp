export function AboutPage() {
  return (
    <section className="page-section">
      <p className="eyebrow">About</p>
      <h2>Auditable natural-language query compiler for finance</h2>
      <p>
        LedgerProof interprets bounded finance questions into constrained QueryPlans. PostgreSQL and Python
        compute values; the model never writes SQL or calculates official totals.
      </p>
      <ul>
        <li>Every material number needs an immutable AnswerReceipt.</li>
        <li>Ambiguous or unsupported questions return no number.</li>
        <li>All records are synthetic Northstar Labs demo data.</li>
      </ul>
    </section>
  );
}
