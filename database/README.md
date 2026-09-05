# Database

The organisers supplied exactly three source tables: `bank`, `account`, and `transaction`.
This directory deliberately does not create vendor, payout, reconciliation, chart-of-accounts,
conversation-log, or feedback tables in the finance database.

## Apply locally

```bash
docker compose up -d mysql redis
python -m pip install -r requirements-tools.txt
python scripts/load_mysql.py --truncate
```

## Important implementation details

- MySQL 8.0+ and InnoDB are the target.
- `transaction` is a SQL keyword; raw SQL must quote it as `` `transaction` ``.
- The fixture session timezone is `+05:30`; application and loader connections must set it.
- `transaction_amount` is an absolute `DECIMAL(15,2)`; direction comes from `transaction_type`.
- `available_balance` is a current account snapshot. It cannot answer historical-balance questions.
- `account_number` and `utr_number` are sensitive. Mask before returning rows to the browser or model.
- Some source IDs are only UUID-like because the provided sample includes a malformed value. Treat IDs as opaque strings instead of coercing every value into a native UUID type.
- `transaction_reference_id` is the default meaning of “reference number.” It is matched exactly and case-sensitively.
- UTR lookup is disabled by default because the field may contain encrypted/tokenized values.

`query_templates.sql` is explanatory. Production query construction belongs in allow-listed
compiler functions with bound parameters and bounded result sizes.
