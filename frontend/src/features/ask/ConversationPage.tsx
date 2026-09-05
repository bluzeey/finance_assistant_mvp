import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import type { AnswerReceipt } from '../../api/generated-types';
import { AnswerCard } from '../../components/answer/AnswerCard';
import { QuestionComposer } from '../../components/chat/QuestionComposer';
import { EvidencePanel } from '../../components/evidence/EvidencePanel';
import sampleReceiptJson from '../../../../contracts/sample_verified_answer_receipt.json';

const useSampleReceipt = import.meta.env.VITE_USE_SAMPLE_RECEIPT === 'true';

export function ConversationPage() {
  const [searchParams] = useSearchParams();
  const [showEvidence, setShowEvidence] = useState(false);
  const draft = searchParams.get('draft');
  const sampleReceipt = useMemo(() => sampleReceiptJson as AnswerReceipt, []);

  return (
    <section className="conversation-layout">
      <div className="conversation-main">
        <div className="conversation-context" aria-live="polite">
          <strong>Server QueryState is authoritative.</strong>
          <span> This scaffold sends drafts to the backend message API in the next vertical slice.</span>
        </div>

        {draft ? (
          <article className="user-turn">
            <span className="eyebrow">Draft question</span>
            <p>{draft}</p>
          </article>
        ) : null}

        {useSampleReceipt ? (
          <AnswerCard receipt={sampleReceipt} onViewEvidence={() => setShowEvidence(true)} />
        ) : (
          <article className="empty-card">
            <h2>Conversation API is ready to connect</h2>
            <p>
              The UI foundation is route-ready. Enable <code>VITE_USE_SAMPLE_RECEIPT=true</code> for the
              contract fixture, or connect the backend conversation/message endpoint when QRY/API work lands.
            </p>
          </article>
        )}

        <QuestionComposer onSubmit={() => undefined} />
      </div>

      {useSampleReceipt && showEvidence ? <EvidencePanel receipt={sampleReceipt} /> : null}
    </section>
  );
}
