---
name: git-flow
description: "Establishes default branching, commit message, and pull-request conventions for a project that doesn't already have its own: Conventional Commits, feature/fix/chore/docs branch prefixes, PR-before-merge, squash-merge by default. Merging always requires an explicit request or human approval, never automatic just because CI is green. Use when starting feature work, committing, or opening or merging a pull request."
---

# Git Flow

## Scope

Governs the mechanics of branching, committing, and merging: when to
branch, how to name it, commit message format, when to open a PR, when
(and whether) to merge it. These are defaults for a project that doesn't
already have its own established conventions — an existing project's own
git conventions always take precedence.

Not for the prose quality of a commit message or PR description's actual
wording — see `technical-writing` for that. The two commonly apply
together: `git-flow` says a commit needs a `feat:` prefix and a body
explaining why; `technical-writing` says how to write that body clearly.

## Branching

- Prefix new branches by the kind of change: `feature/`, `fix/`, `chore/`,
  `docs/`.
- Branch names are kebab-case and describe the change, not the ticket
  number alone: `feature/add-shell-skill`, not `feature/JIRA-123`.

## Commits

- [Conventional Commits](https://www.conventionalcommits.org/): a type
  prefix (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...), an imperative
  summary line, and — for anything non-trivial — a body explaining *why*,
  not just what changed (the diff already shows what).
- Keep commits atomic: one logical change per commit. A commit that mixes
  an unrelated fix with a feature is two commits.
- Whether or not this project versions individual components separately,
  git history is the record of what changed and why. A commit message
  that only restates the diff wastes that record rather than using it.

## Pull requests

- A PR is required before merging to `main` — no direct pushes.
- CI must be green before merge.
- Squash-merge by default, so `main`'s history stays one commit per
  reviewed change.
- **Merging always requires an explicit request or human approval** —
  green CI and no open review threads are necessary conditions, never
  sufficient ones. An explicit request to merge satisfies this on its own;
  silently merging because nothing is technically blocking it does not.

## When a project has its own conventions

These are defaults, not mandates. If the project already has an
established branching model, commit style, or merge process, follow that
instead — don't impose Conventional Commits on a project that already
uses something else.
