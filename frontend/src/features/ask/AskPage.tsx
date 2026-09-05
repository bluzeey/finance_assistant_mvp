import { useNavigate } from 'react-router-dom';

import { QuestionComposer } from '../../components/chat/QuestionComposer';

const examples = [
  'How much did we spend on vendor payouts last month?',
  'How did that compare with the month before?',
  'Who were the top five vendors in August 2026?',
  'Which transactions are still unreconciled?',
  'Show unreconciled items older than 30 days.',
  'Is anything unusual in August payouts?',
];

export function AskPage() {
  const navigate = useNavigate();

  return (
    <section className="ask-empty page-section">
      <div className="hero-card">
        <p className="eyebrow">Ask</p>
        <h2>Ask a finance question. Get the number and its proof.</h2>
        <p>
          Answers are calculated from Northstar Labs’ synthetic transaction, payout, and reconciliation
          data. The assistant cannot invent missing values.
        </p>
      </div>

      <section aria-labelledby="suggested-prompts-title">
        <h3 id="suggested-prompts-title">Suggested prompts</h3>
        <div className="prompt-grid">
          {examples.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => navigate(`/ask/${crypto.randomUUID()}?draft=${encodeURIComponent(example)}`)}
            >
              {example}
            </button>
          ))}
        </div>
      </section>

      <div className="scope-grid">
        <section>
          <h3>Supported</h3>
          <ul>
            <li>Spend and completed vendor payouts</li>
            <li>Vendors, accounts, departments, and dates</li>
            <li>Reconciliation status, open amounts, duplicates, and anomaly callouts</li>
          </ul>
        </section>
        <section>
          <h3>Not supported</h3>
          <ul>
            <li>Forecasts or next-quarter cash-balance projections</li>
            <li>Approvers, payroll, tax advice, or write actions</li>
            <li>Numbers without a verifiable source-row receipt</li>
          </ul>
        </section>
      </div>

      <QuestionComposer
        onSubmit={(message) => navigate(`/ask/${crypto.randomUUID()}?draft=${encodeURIComponent(message)}`)}
      />
    </section>
  );
}
