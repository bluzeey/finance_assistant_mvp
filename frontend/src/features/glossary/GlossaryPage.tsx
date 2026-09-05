import { useQuery } from '@tanstack/react-query';

import { apiGet } from '../../api/client';

export function GlossaryPage() {
  const glossaryQuery = useQuery({
    queryKey: ['glossary'],
    queryFn: ({ signal }) => apiGet<{ items: Array<Record<string, unknown>> }>('/api/v1/glossary', signal),
  });

  return (
    <section className="page-section">
      <p className="eyebrow">Glossary</p>
      <h2>Definitions from semantic contracts</h2>
      {glossaryQuery.isLoading ? <p>Loading glossary…</p> : null}
      {glossaryQuery.isError ? (
        <div className="warning-card">Glossary API unavailable. Definitions remain backend-owned.</div>
      ) : null}
      <div className="glossary-list">
        {(glossaryQuery.data?.items ?? []).slice(0, 12).map((item) => (
          <article className="empty-card" key={String(item.id)}>
            <h3>{String(item.label)}</h3>
            <p>{String(item.description ?? '')}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
