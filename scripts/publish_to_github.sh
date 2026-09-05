#!/usr/bin/env bash
set -euo pipefail

OWNER="${GITHUB_OWNER:-bluzeey}"
REPO="${GITHUB_REPO:-finance_ai_bot}"
VISIBILITY="${GITHUB_VISIBILITY:-private}"
DESCRIPTION="${GITHUB_DESCRIPTION:-Auditable conversational finance assistant for the BVP Tech Catalyst Hackathon}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for executable in git gh python; do
  command -v "$executable" >/dev/null 2>&1 || { echo "Error: $executable is required." >&2; exit 1; }
done

gh auth status >/dev/null 2>&1 || { echo "Error: authenticate GitHub CLI with: gh auth login" >&2; exit 1; }
case "$VISIBILITY" in public|private|internal) ;; *) echo "Invalid visibility: $VISIBILITY" >&2; exit 1;; esac

python scripts/generate_dataset.py --check
python scripts/validate_dataset.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v

if [[ ! -d .git ]]; then
  git init -b main
fi

git config user.name "${GIT_AUTHOR_NAME:-Sahil Maheshwari}"
git config user.email "${GIT_AUTHOR_EMAIL:-sahilm1711@gmail.com}"
git add .
if ! git diff --cached --quiet; then
  git commit -m "Align LedgerProof with Tiby three-table MySQL schema"
fi

REMOTE_URL="https://github.com/$OWNER/$REPO.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  git push -u origin main
else
  gh repo create "$OWNER/$REPO" \
    "--$VISIBILITY" \
    --description "$DESCRIPTION" \
    --source=. \
    --remote=origin \
    --push
fi

echo "Published: https://github.com/$OWNER/$REPO"
