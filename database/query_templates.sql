-- Reference SQL shapes. The backend must compile an allow-listed QueryPlan into these shapes.
-- Never splice user text into SQL. All :parameters are bound values.

-- vendor_payout_amount
SELECT coalesce(sum(p.gross_amount), 0)::numeric(18,2) AS value,
       count(*)::integer AS source_row_count
FROM vendor_payouts p
WHERE p.company_id = :company_id
  AND p.payout_status = 'completed'
  AND p.payout_date >= :start_date
  AND p.payout_date < :end_date_exclusive
  AND (:vendor_ids_is_empty OR p.vendor_id = ANY(:vendor_ids));

-- vendor_payout_amount grouped by vendor
SELECT p.vendor_id, v.display_name AS vendor_name,
       sum(p.gross_amount)::numeric(18,2) AS value,
       count(*)::integer AS source_row_count
FROM vendor_payouts p
JOIN vendors v USING (vendor_id)
WHERE p.company_id = :company_id
  AND p.payout_status = 'completed'
  AND p.payout_date >= :start_date
  AND p.payout_date < :end_date_exclusive
GROUP BY p.vendor_id, v.display_name
ORDER BY value DESC, vendor_name ASC
LIMIT :limit;

-- vendor_spend: signed amount preserves credits and reversals
SELECT coalesce(sum(t.signed_amount), 0)::numeric(18,2) AS value,
       count(*)::integer AS source_row_count
FROM transactions t
JOIN chart_of_accounts coa USING (account_code)
WHERE t.company_id = :company_id
  AND t.status = 'posted'
  AND coa.account_type IN ('Expense','COGS')
  AND t.posting_date >= :start_date
  AND t.posting_date < :end_date_exclusive
  AND (:vendor_ids_is_empty OR t.vendor_id = ANY(:vendor_ids))
  AND (:account_codes_is_empty OR t.account_code = ANY(:account_codes));

-- open reconciliation: use unreconciled_amount, not full transaction amount
SELECT r.transaction_id, t.posting_date, t.vendor_id, v.display_name AS vendor_name,
       r.status, r.unreconciled_amount, r.reason_code, r.owner
FROM reconciliation_status r
JOIN transactions t USING (transaction_id)
JOIN vendors v USING (vendor_id)
WHERE r.company_id = :company_id
  AND t.status = 'posted'
  AND r.status IN ('unreconciled','partially_reconciled','disputed')
  AND (:before_date_is_null OR t.posting_date < :before_date)
ORDER BY t.posting_date ASC, r.transaction_id ASC
LIMIT :limit;

-- possible duplicate candidates; warning only, not a financial adjustment
SELECT p1.payout_id AS payout_id_a, p2.payout_id AS payout_id_b,
       p1.vendor_id, p1.payout_date, p1.gross_amount,
       p1.bank_reference, p1.invoice_reference
FROM vendor_payouts p1
JOIN vendor_payouts p2
  ON p1.company_id = p2.company_id
 AND p1.vendor_id = p2.vendor_id
 AND p1.payout_date = p2.payout_date
 AND p1.gross_amount = p2.gross_amount
 AND p1.payout_id < p2.payout_id
 AND (
   (p1.bank_reference IS NOT NULL AND p1.bank_reference = p2.bank_reference)
   OR p1.invoice_reference = p2.invoice_reference
 )
WHERE p1.company_id = :company_id
  AND p1.payout_status = 'completed'
  AND p2.payout_status = 'completed';
