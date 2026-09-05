import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import sampleReceiptJson from '../../../../contracts/sample_verified_answer_receipt.json';
import type { AnswerReceipt } from '../../api/generated-types';
import { AnswerCard } from './AnswerCard';

const sampleReceipt = sampleReceiptJson as AnswerReceipt;

describe('AnswerCard', () => {
  it('renders receipt-owned number, lineage, and validation status', () => {
    render(<AnswerCard receipt={sampleReceipt} />);

    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('₹1,00,00,874.04')).toBeInTheDocument();
    expect(screen.getByText('53 source records')).toBeInTheDocument();
    expect(screen.getByText(/Data through 2026-09-03/)).toBeInTheDocument();
  });
});
