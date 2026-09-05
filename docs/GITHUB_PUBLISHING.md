# GitHub Publishing

The intended repository is:

```text
bluzeey/finance_ai_bot
```

The GitHub repository must exist before a content-only connector can push. The supplied helper can
create it when the authenticated GitHub CLI account has repository-creation permission.

## One-command publication

From the repository root:

```bash
bash scripts/publish_to_github.sh
```

Defaults:

- owner: `bluzeey`
- repository: `finance_ai_bot`
- visibility: private
- branch: `main`

Override with environment variables:

```bash
GITHUB_OWNER=bluzeey \
GITHUB_REPO=finance_ai_bot \
GITHUB_VISIBILITY=private \
bash scripts/publish_to_github.sh
```

The script runs fixture determinism, dataset, repository and unit-test checks before committing and
pushing.

## Manual path

Create an empty repository without README, `.gitignore` or license, then:

```bash
git init -b main
git add .
git commit -m "Align LedgerProof with Tiby three-table MySQL schema"
git remote add origin https://github.com/bluzeey/finance_ai_bot.git
git push -u origin main
```

Using GitHub CLI:

```bash
gh repo create bluzeey/finance_ai_bot \
  --private \
  --description "Auditable conversational finance assistant for the BVP Tech Catalyst Hackathon" \
  --source=. \
  --remote=origin \
  --push
```

## Before publication

```bash
python -m pip install -r requirements-tools.txt
python scripts/generate_dataset.py --check
python scripts/validate_dataset.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v
```

Confirm that `.env`, API keys, database dumps, model payloads, exports and local evaluation runs are
not staged:

```bash
git status --short
git ls-files | grep -E '(^|/)(\.env|exports|runs)(/|$)' && exit 1 || true
```

## Recommended repository settings

- keep private during the hackathon unless public submission is required;
- enable pull requests and Actions;
- require the fixture/contract validation workflow before merge once collaboration begins;
- squash-merge task branches;
- use ticket IDs from `project_backlog.csv` in PR titles;
- do not store production/real financial data in the repository.

## Release bundle

Create the source archive with:

```bash
python scripts/build_bundle.py --output /mnt/data/finance_ai_bot.zip
```

The archive is deterministic and excludes secrets, Git metadata, caches, node modules and runtime
exports. Record its SHA-256 when handing it to another agent.
