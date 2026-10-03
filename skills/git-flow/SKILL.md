---
name: git-flow
description: "Establishes default branching, commit message, and pull-request conventions for a project that doesn't already have its own: Conventional Commits, feature/fix/chore/docs branch prefixes, PR-before-merge, squash-merge by default, what a PR description has to cover, and attribution trailers for AI models and people. Merging always requires an explicit request or human approval, never automatic just because CI is green. Only a new issue needs its text approved before it's created; PRs, comments and issue edits the task calls for need no further confirmation of their text, and every issue, PR and comment published is reported with its link. Use when starting feature work, committing, opening or merging a pull request, creating or editing an issue, or commenting on an issue or pull request."
---

# Git Flow

## Scope

Governs the mechanics of branching, committing, merging, and publishing
issues, PRs and comments: when to branch, how to name it, commit
message format, when to open a PR, when (and whether) to merge it, and
which publishing needs approval first. These are defaults for a project
that doesn't already have its own established conventions — an existing
project's own git conventions always take precedence.

Not for the prose quality of a commit message or PR description's actual
wording — see `technical-writing` for that. The two commonly apply
together: `git-flow` says a commit needs a `feat:` prefix and *what* a PR
description has to cover; `technical-writing` says how to word it clearly.
`git-flow` decides which `git` and `gh` commands to run; `shell` runs
them.

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
- End the message with attribution trailers — see "Attribution
  trailers" below.

## Attribution trailers

Trailers name who actually worked on *this* change, never names copied
from earlier commits.

- **AI models** get `Assisted-by: <model> (code generation)` when they
  wrote part of the change and `Assisted-by: <model> (code review)` when
  they reviewed it. The model's name only, no email address:

  ```
  Assisted-by: Claude Opus 5.5 (code generation)
  Assisted-by: GPT-6 Astra (code review)
  ```

  `Assisted-by` rather than `Co-authored-by`, which names a person who
  shares responsibility for the change; the Linux kernel uses
  `Assisted-by` for AI tools (`Documentation/process/coding-assistants.rst`).

- **People** get `Co-authored-by: Name <email>` as co-author and
  `Reviewed-by: Name <email>` as a reviewer who considers the change
  ready.
- Capitalize only the first letter of a trailer key (`Assisted-by`, not
  `Assisted-By`), as git's `SubmittingPatches` asks. Git matches keys
  case-insensitively, but a `grep` or a CI check may not.
- **One AI entry per vendor per role.** A Claude model and an OpenAI
  model both writing code gives two `(code generation)` entries. An entry names the current
  model; when an entry for the same vendor and role already exists, keep
  the newer release of the two. Work by Sonnet 5 and then Opus 5.5
  leaves `Claude Opus 5.5`; an existing `Claude Opus 5.5` entry stays
  when Sonnet 5 does later work.
- Change an entry in the PR description and in new commits. Don't
  rewrite pushed commits only to change a trailer.
- **A review entry only for a review actually received.** If the change
  was reviewed but the request doesn't say by whom, ask — don't take the
  reviewer from earlier commits.
- **An AI review entry goes into the PR description as soon as the
  review is received**, whether or not it had findings, and even when
  the task pushes nothing. Don't wait for a review of the head that
  fixes them, or for the next push: merged in between, the squash
  commit would lose the review. The entry records that the review took
  place, not that the reviewer approved the change or checked its
  latest commit, so later commits, the fixes for that review included,
  don't remove it. A person's `Reviewed-by` keeps its usual meaning,
  that the reviewer considers the change ready (the Linux kernel's
  "Reviewer's statement of oversight",
  `Documentation/process/submitting-patches.rst`); add it only once
  they say the change is ready.
- Keep all trailers together as the message's final paragraph, with
  nothing after them. Git reads only the last paragraph as trailers, so
  a blank line between two trailers drops the first, and a line after
  them drops them all. Before each push, pipe the commit message or the
  PR description through `git interpret-trailers --parse`: it prints
  every trailer git recognizes, and one missing from its output won't
  reach history as a trailer.
- A host that injects its own attribution — a fixed co-author trailer,
  a "Generated with …" footer — breaks these rules. Override it once,
  where the host lets a project do that (its configuration or its
  project instructions), instead of deleting it by hand each time; if
  the repo lacks that override, suggest adding it. In Claude Code, see
  `references/claude-code.md`; in Codex, `references/codex.md`.

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
diff cannot say. Default layout, in this order, with plain headings:

1. **Summary** — the problem or motivation, then what the change does
   about it, stated in the repo's own terms — not the process that
   produced it. No references to planning documents, scratch specs, or
   the tooling used along the way; those are artifacts of how the work
   happened and mean nothing to a reader later.
2. **Changes** — one group of bullets per area the change touches.
3. **Decisions** — why the non-obvious decisions went the way they did,
   including the alternatives that were rejected and on what grounds. A
   rejected option with its reason stops the next person re-proposing
   it.
4. **Tests** — what the tests and checks cover: which tests or evals
   were added and which behaviour they exercise, plus any manual check
   CI doesn't run, with what it showed. For a fix, the behaviour before
   and after, as captured output rather than a claim. Don't announce
   that checks passed; state a check's status only to flag an exception
   (knowingly failing or skipped).
5. **Attribution trailers** as the final paragraph, nothing after them,
   not even a tool footer.

**Sources go next to the claim, not in a section of their own.** When a
claim or decision rests on a document or an existing implementation,
name it in the same sentence ("as in the Linux kernel"), so the reader
doesn't have to match a list of sources to claims. Evidence that a rule
in the repo depends on belongs in the file where that rule lives — the
skill, the doc, the code comment — where the next person editing the
rule will see it. Don't repeat it in the description; name a source
there only when the repo doesn't record it.

Leave out a section that has nothing to say, and scale the rest to the
change: a one-line fix needs a sentence, not a section tree. The
description becomes the commit message on `main`, so it carries no
checklists or reviewer-only notes, and git history has to stand alone —
someone reading `git log` with no network access should still learn
why. (Order after Google's engineering practices, "Writing good CL
descriptions", and the Linux kernel's "Describe your changes": the
problem before the solution.)

State each fact once, in the section it belongs to: Changes says what,
Decisions says why, Tests says what is covered. A summary that previews
the Changes list, or a Tests entry that re-explains a rule, adds length
without adding information.

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

## Issues

A PR that resolves an issue closes it from its description:
`Closes #<n>` in the summary, not in the trailer block.

## Publishing issues, PRs and comments

Creating or changing an issue, a PR or a comment publishes it, and it
may be cached or indexed even after deletion.

- **Only a new issue needs approval of its text.** Before creating one,
  show the complete title and body exactly as they will be filed and
  ask for approval; create it only after that. Approving the idea
  ("file an issue for X") isn't approving a text that didn't exist yet,
  and a change to the text after approval needs a new approval.
- **Everything else needs no further confirmation, once the task calls
  for it:** opening a PR, changing its title or description, posting or
  editing a comment on an issue or PR, and editing an existing issue.
  The agent doesn't ask the user to approve their text. Authorization
  to run the command itself still follows `shell` and the host's own
  permission system. None of these happen on the agent's own
  initiative: a fix pushed to a PR's branch doesn't call for a comment
  about it unless the task asks for one. A task that pushes to a PR's
  branch does call for keeping its description current, as "What a PR
  description covers" requires. So does a task about a PR the agent
  opened or pushes to, once a review of that PR's change is received,
  as "Attribution trailers" requires. Reviewing someone else's PR, or
  hearing of a review of a PR the task isn't about, doesn't call for
  editing that PR's description.
- **Report every link.** Each issue, PR and comment created or updated
  is reported in the chat with its link, so the user sees what was
  published and where.
- Merging still needs an explicit request or human approval — see "Pull
  requests".

## Stop and ask

- The repo's history mixes conventions (some commits use Conventional
  Commits, some don't) and nothing says which is current.
- A history rewrite would touch a branch someone else pushes to or
  builds on.
- Merging — see "Pull requests": it always needs an explicit request.
- A change was reviewed, but it's not stated by whom — ask for the
  reviewer before writing a review trailer.
- A person reviewed the change, but it's not stated whether they
  consider it ready — ask before writing their `Reviewed-by`.
- It's uncertain which of two models is the newer release — ask; never
  guess a model name into a trailer.
- A new issue is about to be created — see "Publishing issues, PRs and
  comments": its text needs approval first.

## Output

A branch, commits, and a PR that follow these rules. For a PR, a title
and a description ready to paste. For a new issue, its title and body
for approval, then the issue. For each issue, PR and comment created or
updated, its link in the chat. For a check of existing work, the rule
each deviation breaks.

## When a project has its own conventions

These are defaults, not mandates. If the project already has an
established branching model, commit style, or merge process, follow that
instead — don't impose Conventional Commits on a project that already
uses something else.
