# Publishing to GitHub

The intended repository is `bluzeey/finance_ai_bot`.

## Automated path

From the repository root, with GitHub CLI authenticated:

```bash
GITHUB_VISIBILITY=private ./scripts/publish_to_github.sh
```

Use `GITHUB_VISIBILITY=public` for a public hackathon repository.

The script:

1. validates the fixture and repository contracts;
2. initializes Git when necessary;
3. commits all tracked project files;
4. creates `bluzeey/finance_ai_bot` when it does not exist; and
5. pushes `main`.

Optional overrides:

```bash
GITHUB_OWNER=bluzeey \
GITHUB_REPO=finance_ai_bot \
GITHUB_VISIBILITY=private \
GIT_AUTHOR_NAME="Sahil Maheshwari" \
GIT_AUTHOR_EMAIL="sahilm1711@gmail.com" \
./scripts/publish_to_github.sh
```

## Manual path

Create an empty GitHub repository named `finance_ai_bot` without a generated README, license, or `.gitignore`. Then run:

```bash
git init -b main
git add .
git commit -m "Initialize LedgerProof finance assistant hackathon project"
git remote add origin https://github.com/bluzeey/finance_ai_bot.git
git push -u origin main
```

## Importing the supplied Git bundle

A Git bundle preserves the prepared initial commit:

```bash
git clone finance_ai_bot.gitbundle finance_ai_bot
cd finance_ai_bot
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/bluzeey/finance_ai_bot.git
git push -u origin main
```

## Safety notes

- Keep `.env` out of source control; only `.env.example` belongs in Git.
- The dataset is synthetic, but the repository can remain private until submission.
- Do not add real bank, ERP, vendor, employee, or customer information.
- Do not claim benchmark accuracy or 20M-record performance until measured.
