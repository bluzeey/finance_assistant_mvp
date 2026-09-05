#!/usr/bin/env python3
"""Validate repository structure, contracts, backlog, source alignment and gold isolation."""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "project_backlog.csv",
    "docs/PROVIDED_DATABASE_SCHEMA.md",
    "docs/SCHEMA_ALIGNMENT_AND_GAPS.md",
    "docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md",
    "docs/UI_UX_SPEC.md",
    "docs/BACKEND_QUERY_ENGINE_SPEC.md",
    "docs/BUG_AND_QA_PLAYBOOK.md",
    "docs/SECURITY_PRIVACY_AND_TRUST.md",
    "docs/MODEL_EVALUATION_PLAN.md",
    "docs/AGENT_EXECUTION_PLAN.md",
    "contracts/openapi.yaml",
    "contracts/query_plan.schema.json",
    "contracts/answer_receipt.schema.json",
    "contracts/semantic_metrics.yaml",
    "contracts/sample_verified_answer_receipt.json",
    "data/dataset_manifest.json",
    "data/csv/bank.csv",
    "data/csv/account.csv",
    "data/csv/transaction.csv",
    "data/csv/data_dictionary.csv",
    "database/schema.sql",
    "database/indexes.sql",
    "database/provided_sample_seed.sql",
    "scripts/generate_dataset.py",
    "scripts/load_mysql.py",
    "scripts/validate_dataset.py",
]
errors: list[str] = []
warnings: list[str] = []

for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f"missing required file: {rel}")

# JSON and JSON Schema.
schemas: dict[Path, dict] = {}
for path in sorted((ROOT / "contracts").glob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if path.name.endswith(".schema.json"):
            schemas[path] = data
    except Exception as exc:  # pragma: no cover - diagnostic path
        errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")

try:
    from jsonschema import Draft202012Validator  # type: ignore
except ImportError:
    Draft202012Validator = None
    warnings.append("jsonschema not installed; meta-schema/sample checks skipped")

if Draft202012Validator:
    for path, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"invalid JSON Schema {path.relative_to(ROOT)}: {exc}")
    try:
        sample = json.loads((ROOT / "contracts/sample_verified_answer_receipt.json").read_text(encoding="utf-8"))
        receipt_schema = json.loads(json.dumps(schemas[ROOT / "contracts/answer_receipt.schema.json"]))
        # Inline the local computation reference so validation is offline and does not
        # depend on URI resolver behavior across jsonschema versions.
        computed_schema = schemas[ROOT / "contracts/computed_facts.schema.json"]
        receipt_schema["properties"]["computation"] = {"oneOf": [{"type": "null"}, computed_schema]}
        for issue in sorted(Draft202012Validator(receipt_schema).iter_errors(sample), key=lambda e: list(e.path)):
            errors.append(f"sample receipt schema error at {list(issue.path)}: {issue.message}")
    except Exception as exc:
        errors.append(f"could not validate sample receipt: {exc}")

# YAML/OpenAPI parse.
try:
    import yaml  # type: ignore
except ImportError:
    yaml = None
    warnings.append("PyYAML not installed; YAML parse checks skipped")

if yaml:
    for rel in ["contracts/openapi.yaml", "contracts/semantic_metrics.yaml"]:
        try:
            parsed = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
            if not isinstance(parsed, dict):
                errors.append(f"YAML root is not an object: {rel}")
        except Exception as exc:
            errors.append(f"invalid YAML {rel}: {exc}")

# Exact source file and MySQL alignment.
csv_names = {p.name for p in (ROOT / "data/csv").glob("*.csv")}
expected_csv = {"bank.csv", "account.csv", "transaction.csv", "data_dictionary.csv"}
if csv_names != expected_csv:
    errors.append(f"source CSV set must be exactly {sorted(expected_csv)}, found {sorted(csv_names)}")

schema_path = ROOT / "database/schema.sql"
if schema_path.exists():
    schema_text = schema_path.read_text(encoding="utf-8")
    created = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z_]+)`?", schema_text, re.I)
    if created != ["bank", "account", "transaction"]:
        errors.append(f"database/schema.sql must create bank, account, transaction in order; found {created}")
    for token in ["ENGINE=InnoDB", "ENUM('credit','debit')", "TIMESTAMP(6)", "DECIMAL(15,2)"]:
        if token not in schema_text:
            errors.append(f"database/schema.sql missing MySQL source token: {token}")

for obsolete in [
    "scripts/load_postgres.py",
    "data/csv/vendors.csv",
    "data/csv/vendor_payouts.csv",
    "data/csv/reconciliation_status.csv",
    "data/csv/chart_of_accounts.csv",
    "database/views.sql",
]:
    if (ROOT / obsolete).exists():
        errors.append(f"obsolete richer-schema artifact exists: {obsolete}")

# Backlog IDs, dependencies and cycles.
try:
    with (ROOT / "project_backlog.csv").open(newline="", encoding="utf-8") as handle:
        tasks = list(csv.DictReader(handle))
    required_cols = {
        "ticket_id", "epic", "title", "description", "priority", "phase", "owner_role",
        "dependencies", "acceptance_criteria", "tests_required", "estimate_points", "status", "files_area",
    }
    if not tasks or set(tasks[0]) != required_cols:
        errors.append("project_backlog.csv columns do not match the required contract")
    ids = [t["ticket_id"] for t in tasks]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ticket IDs in project_backlog.csv")
    idset = set(ids)
    graph: dict[str, set[str]] = defaultdict(set)
    indegree = {ticket_id: 0 for ticket_id in ids}
    for task in tasks:
        tid = task["ticket_id"]
        deps = [d.strip() for d in task.get("dependencies", "").split(";") if d.strip()]
        for dep in deps:
            if dep not in idset:
                errors.append(f"unknown dependency {dep} on {tid}")
                continue
            if dep == tid:
                errors.append(f"self dependency on {tid}")
                continue
            if tid not in graph[dep]:
                graph[dep].add(tid)
                indegree[tid] += 1
        if task.get("priority") not in {"P0", "P1", "P2"}:
            errors.append(f"invalid priority on {tid}")
        if task.get("status") not in {"todo", "doing", "blocked", "review", "done"}:
            errors.append(f"invalid status on {tid}")
        if not task.get("acceptance_criteria") or not task.get("tests_required"):
            errors.append(f"missing acceptance/tests on {tid}")
    queue = deque(sorted(k for k, v in indegree.items() if v == 0))
    visited = 0
    while queue:
        node = queue.popleft(); visited += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if visited != len(ids):
        errors.append("dependency cycle in project_backlog.csv")
except Exception as exc:
    errors.append(f"could not validate backlog: {exc}")

# Generated/cached files may be created by validation itself. They are ignored by Git
# and excluded by the bundle builder. Fail only when Git reports them as tracked.
try:
    import subprocess
    tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).splitlines())
except Exception:
    tracked = set()
for rel in tracked:
    parts = Path(rel).parts
    if "__pycache__" in parts or Path(rel).suffix.lower() in {".pyc", ".pyo"}:
        errors.append(f"generated bytecode is tracked: {rel}")

# Runtime code cannot read evaluation gold.
for base in [ROOT / "backend", ROOT / "frontend"]:
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"evaluation[\\/]expected_|expected_aggregates|benchmark_cases\.jsonl", text):
            errors.append(f"runtime gold dependency: {path.relative_to(ROOT)}")

# Targeted stale-plan checks. Migration/gap docs may mention PostgreSQL historically.
stale_checks = {
    "backend/README.md": ["PostgreSQL", "completed vendor payouts", "/reconciliation"],
    "frontend/README.md": ["payouts table", "/reconciliation"],
    "docs/AGENT_EXECUTION_PLAN.md": ["PostgreSQL", "vendor_payout_amount", "open reconciliation compiler"],
    "docs/DEVELOPMENT_RUNBOOK.md": ["load_postgres.py", "docker compose up -d postgres"],
    "docs/DEMO_AND_SUBMISSION_PLAN.md": ["SUM(gross_amount)", "reconciliation proof"],
    "project_backlog.csv": ["PostgreSQL", "Reconciliation KPIs", "Open reconciliation compiler"],
}
for rel, needles in stale_checks.items():
    path = ROOT / rel
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    for needle in needles:
        if needle.lower() in text:
            errors.append(f"stale richer-schema phrase in {rel}: {needle}")

# Basic internal Markdown link existence for relative repo links.
link_pattern = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
for path in [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for target in link_pattern.findall(text):
        clean = target.split("#", 1)[0].strip()
        if not clean or clean.startswith("sandbox:"):
            continue
        candidate = (path.parent / clean).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"link escapes repository in {path.relative_to(ROOT)}: {target}")
            continue
        if not candidate.exists():
            errors.append(f"broken relative link in {path.relative_to(ROOT)}: {target}")

for warning in warnings:
    print(f"WARN: {warning}")
if errors:
    print("Repository validation FAILED:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

print("PASS: repository structure, MySQL source alignment, contracts, sample receipt, backlog DAG, links, and runtime/gold isolation are valid.")
