---
name: git-flow
description: "Establishes default branching, commit message, and pull-request conventions for a project that doesn't already have its own: Conventional Commits, feature/fix/chore/docs branch prefixes, PR-before-merge, squash-merge by default, and what a PR description has to cover. Merging always requires an explicit request or human approval, never automatic just because CI is green. Use when starting feature work, committing, or opening or merging a pull request."
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
together: `git-flow` says a commit needs a `feat:` prefix and *what* a PR
description has to cover; `technical-writing` says how to word it clearly.

When checking repo state for these conventions, pull only what's
needed — `git log --oneline -N`, not a full history dump; the relevant
hunk, not an entire diff, when just confirming a *format* convention is
followed. Atomicity is the exception: whether a commit mixes two
logical changes is not visible in one hunk, so check that against the
commit's full file list or diff.

## Branching

- Prefix new branches by the kind of change: `feature/`, `fix/`, `chore/`,
  `docs/`.
- Branch names are kebab-case and describe the change, not the ticket
  number alone: `feature/add-shell-skill`, not `feature/JIRA-123`.

## Commits

- [Conventional Commits](https://www.conventionalcommits.org/): a type
  prefix (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...), an imperative
  summary line, and — for anything non-trivial — a body explaining *why*,
  not just what changed (the diff already shows what). Hard-wrap the
  body at about 72 columns.
- Keep commits atomic: one logical change per commit. A commit that mixes
  an unrelated fix with a feature is two commits.
- Whether or not this project versions individual components separately,
  git history is the record of what changed and why. A commit message
  that only restates the diff wastes that record rather than using it.
- Attribution trailers name who actually worked on *this* change — its
  reviewers and co-authors — never names copied from earlier commits.
  Their token spelling and order follow the repo's existing history; a
  second spelling of the same trailer makes the history look like two
  projects.
- Keep all trailers together as the message's final paragraph, with
  nothing after them. Git reads only the last paragraph as trailers
  (`git interpret-trailers --parse`), so a blank line between two
  trailers drops the first, and a line after them drops them all.

## Pull requests

- A PR is required before merging to `main` — no direct pushes.
- CI must be green before merge.
- Squash-merge by default, so `main`'s history stays one commit per
  reviewed change, with the squash commit set to take the PR title as
  its subject and the PR description as its body (on GitHub: "Default
  to pull request title and description"; its own default instead uses
  a single-commit PR's commit message). The PR title therefore follows
  the commit rules above, type prefix included, and the description
  ends with the attribution trailers as its final paragraph.
- Branch commits don't reach `main` under that setting, but reviewers
  read them, so they follow the commit rules too — trailers included.
- Rewriting a pushed branch (amend, rebase) needs
  `git push --force-with-lease=<branch>:<expected-sha>`, never a bare
  `--force`, and only on a branch no one else pushes to or builds on.
  The lease makes the push fail instead of overwriting commits you
  haven't seen.
- **Merging always requires an explicit request or human approval** —
  green CI and no open review threads are necessary conditions, never
  sufficient ones. An explicit request to merge satisfies this on its own;
  silently merging because nothing is technically blocking it does not.

## What a PR description covers

The diff already shows what changed. The description exists for what the
diff cannot say, and it covers four things:

- **What this PR adds to the repo**, stated in the repo's own terms — not
  the process that produced it. No references to planning documents,
  scratch specs, or the tooling used along the way; those are artifacts
  of how the work happened and mean nothing to a reader later.
- **Why the non-obvious decisions went the way they did**, including the
  alternatives that were rejected and on what grounds. A rejected option
  with its reason stops the next person re-proposing it.
- **Where factual claims come from.** If a claim rests on a document or
  an existing implementation, name it rather than asserting it.
- **Testing**: what the tests and checks cover — which tests or evals
  were added and which behaviour they exercise, plus any manual check CI
  doesn't run, with what it showed. Don't announce that checks passed;
  state a check's status only to flag an exception (knowingly failing
  or skipped).

Scale this to the change: a one-line fix needs a sentence, not a section
tree. The description becomes the commit message on `main`, and git
history has to stand alone — someone reading `git log` with no network
access should still learn why. End it with the attribution trailers and
nothing after them, not even a tool footer.

**The description states the branch as it is now, not how it got
there.** After every push — above all one that answers a review — and
after every rebase, re-derive each claim from `git diff <target>...HEAD`
and re-measure every number instead of copying it forward. When a change
is no longer part of the branch, delete its section; don't reword it or
append a correction. A PR description is not a log of review rounds. A
commit hash it cites comes from `git rev-parse --short HEAD` after the
push, never from memory.

**Wrapping:** GitHub renders every newline in a PR description, review
comment, issue body, or release note as a line break. Write each
paragraph and list item there as one line; the squash commit carries
the description to `main` unwrapped, and the 72-column rule applies to
commits written on the branch. A commit body is hard-wrapped, so join
its paragraphs before reusing it as a PR description, keeping its
trailers as the final block.

## Stop and ask

- The repo's history mixes conventions (some commits use Conventional
  Commits, some don't) and nothing says which is current.
- A history rewrite would touch a branch someone else pushes to or
  builds on.
- Merging — see "Pull requests": it always needs an explicit request.

## Output

A branch, commits, and a PR that follow these rules. For a PR, a title
and a description ready to paste. For a check of existing work, the rule
each deviation breaks.

## When a project has its own conventions

These are defaults, not mandates. If the project already has an
established branching model, commit style, or merge process, follow that
instead — don't impose Conventional Commits on a project that already
uses something else.
