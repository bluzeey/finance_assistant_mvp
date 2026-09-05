# Deterministic Query Catalogue

Each executable QueryPlan maps to a server-owned query family. User/model text never becomes SQL.

| Family | Metric/intent | Source | Main filters | Proof checks |
|---|---|---|---|---|
| `TX_FLOW_TOTAL_V1` | debit/credit total | transaction + account/bank when needed | half-open date, type, bank, program, account, entity, amount | Decimal, row/account count, date bounds, lineage |
| `TX_NET_FLOW_V1` | credit minus debit | transaction | same | component reconciliation, Decimal, lineage |
| `TX_COUNT_AVG_V1` | count/average | transaction | same | count, average policy, lineage |
| `TX_EXTREME_V1` | largest transaction | transaction | same | stable tie order, source row, privacy |
| `TX_GROUP_V1` | grouped total/count | transaction + account + bank | same; group enum | group sum=count reconciliation, stable ordering |
| `TX_COMPARE_V1` | previous/custom comparison | two TX plans | two half-open ranges | both subreceipts, zero baseline policy |
| `TX_ID_LOOKUP_V1` | transaction ID lookup | transaction | exact opaque ID | 0/1 row, privacy |
| `TX_REFERENCE_LOOKUP_V1` | reference lookup | transaction | exact case-sensitive reference | 0/1/many, duplicate qualification |
| `TX_DESCRIPTION_SEARCH_V1` | literal narration search | transaction | bounded literal text plus normal filters | qualification, redaction, injection safety |
| `ACCOUNT_BALANCE_V1` | current available balance/account count | account + bank | bank, program, account, entity | snapshot qualification, Decimal, account lineage |
| `SOURCE_RECORDS_V1` | receipt records | persisted plan | cursor/page size | union/hash/count parity, privacy |

Every family must declare:

- required and optional QueryPlan fields;
- fixed SQL identifiers/operators/functions;
- stable ordering and pagination key;
- expected result shape;
- required validations and warning codes;
- source ID/hash procedure;
- supported indexes and performance budget.

Unsupported/clarification/no-data are typed constructors and do not execute a fallback broad query.
