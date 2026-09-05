#!/usr/bin/env bash
set -euo pipefail

OWNER="${GITHUB_OWNER:-bluzeey}"
REPO="${GITHUB_REPO:-finance_ai_bot}"
VISIBILITY="${GITHUB_VISIBILITY:-private}"
DESCRIPTION="${GITHUB_DESCRIPTION:-Auditable conversational finance assistant for the BVP Tech Catalyst Hackathon}"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required." >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is required: https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: GitHub CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

case "$VISIBILITY" in
  public|private|internal) ;;
  *)
    echo "Error: GITHUB_VISIBILITY must be public, private, or internal." >&2
    exit 1
    ;;
esac

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python scripts/validate_dataset.py
python scripts/validate_repository.py

if [[ ! -d .git ]]; then
  git init -b main
fi

git config user.name "${GIT_AUTHOR_NAME:-Sahil Maheshwari}"
git config user.email "${GIT_AUTHOR_EMAIL:-sahilm1711@gmail.com}"
git add .
if ! git diff --cached --quiet; then
  git commit -m "Initialize LedgerProof finance assistant hackathon project"
fi

if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "Repository $OWNER/$REPO already exists."
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "https://github.com/$OWNER/$REPO.git"
  else
    git remote add origin "https://github.com/$OWNER/$REPO.git"
  fi
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
