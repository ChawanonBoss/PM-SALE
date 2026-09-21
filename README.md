# PM-SALE

Single-file web app (`index.html`, no build step) for sales/project management: sales & projects with SO/PJ document numbers, Action Plan (Gantt),
warehouse with serial numbers and withdrawal history, warranty tracking, customers, company letterheads, product catalogs (PDF), project attachments,
Excel export, users with admin approval, audit log and trash. Thai UI, Firebase (Auth + Firestore) backend shared with BU-ABB (collections are `pm_`-prefixed).

- Live: https://chawanonboss.github.io/PM-SALE/ (GitHub Pages serves the repo root)
- `firestore.rules` is a **reference copy of the PM-SALE part only** - the live rules are one file per Firebase project (merged with BU-ABB's) and must be pasted in the Console by hand.
- `APP_VERSION` (top of the script) is bumped on every push: last digit for changes that do not touch the site's structure, middle digit (last reset to 0) for new pages / collections / data fields.
- `docs/handover-template.docx` is the Word template the handover PDF was built from. Tests: see `tests/README.md`. Working notes for Claude Code: `CLAUDE.md`.
