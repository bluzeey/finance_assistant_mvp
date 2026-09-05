import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createQueryClient } from './query-client';
import { routes } from './router';

function renderRoute(initialEntry: string) {
  const router = createMemoryRouter(routes, { initialEntries: [initialEntry] });
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(mockFetch));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('router', () => {
  it('renders the Ask empty state', async () => {
    renderRoute('/ask');
    expect(
      await screen.findByText('Ask a finance question. Get the number and its proof.'),
    ).toBeInTheDocument();
  });

  it('renders the data health route', async () => {
    renderRoute('/data-health');
    expect(
      await screen.findByText('Freshness, coverage, integrity, and quality checks'),
    ).toBeInTheDocument();
    expect(await screen.findByText('Posted transactions have reconciliation coverage')).toBeInTheDocument();
  });
});

function mockFetch(input: RequestInfo | URL): Response {
  const url = String(input);
  if (url.endsWith('/api/v1/meta')) {
    return jsonResponse({
      company: {
        company_id: 'CMP-NL-001',
        display_name: 'Northstar Labs',
        currency: 'INR',
        timezone: 'Asia/Kolkata',
        fiscal_year_start_month: 4,
        synthetic: true,
      },
      dataset: {
        version: '2026.09.04-hackathon-v1',
        data_as_of: '2026-09-03',
        max_posting_date: '2026-09-03',
        max_payout_date: '2026-09-03',
        freshness_state: 'fresh',
      },
      supported_metrics: [],
      supported_examples: [],
      features: { evaluation_enabled: false },
    });
  }
  if (url.endsWith('/api/v1/data-health')) {
    return jsonResponse({
      overall_state: 'warning',
      data_as_of: '2026-09-03',
      checks: [
        {
          check_id: 'DH-MISSING-RECONCILIATION',
          category: 'coverage',
          status: 'warning',
          label: 'Posted transactions have reconciliation coverage',
          details: '1 posted transaction has no reconciliation-status record.',
          affected_record_count: 1,
          sample_record_ids: ['TXN-MISSING-REC-001'],
        },
      ],
    });
  }
  return jsonResponse({ message: 'not found' }, 404);
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
