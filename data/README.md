# Synthetic Finance Dataset

The CSV fixture represents one fictitious company, Northstar Labs India Private Limited, in INR and Asia/Kolkata. It is deterministic and safe to publish.

Run:

```bash
python scripts/validate_dataset.py
```

See `docs/DATASET_GUIDE.md` for table semantics, relationships, planted edge cases, exact date anchor, and supported metrics. Do not manually edit generated CSVs; modify `scripts/generate_dataset.py`, regenerate, validate, and review the manifest.
