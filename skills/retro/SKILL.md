---
name: retro
description: "Reviews the current session (or a described problem within it) and proposes skill updates, new skills, or bug reports as GitHub issues — each shown concretely before a per-item choice to implement now or just record the proposal. Edits target the relevant skill's actual source repo, never an installed plugin cache. Use when the user asks for a retro, a lessons-learned pass, or a review of what went wrong in a session, or when a session with notable friction is wrapping up."
---

# Retro

## Scope

Reviews a session (the current one, or a described problem within it) for
things worth carrying forward: an existing skill that should change, a gap
that needs a new skill, or a bug worth filing as a GitHub issue.

Not a substitute for `skill-writing`'s own authoring conventions: when a
proposal is a skill-update, drafting the actual `SKILL.md` content still
follows `skill-writing`'s naming/description/progressive-disclosure rules.
Not a substitute for `git-flow`'s conventions either: applying a proposal
means a real commit/PR in the target repo, and `git-flow`'s rules (branch
prefix, commit format, PR-before-merge, never auto-merge) apply to that
commit/PR the same as any other. Filing an issue or running `gh`/`git`
commands goes through `shell`, the same as any other shell command.
Drafting a proposal's actual prose — a bug-issue's title and body, or a
skill-update's rationale — follows `technical-writing`'s clarity rules,
the same as any other technical writing.

## Procedure

1. **Review.** Look at the session (or the described problem) for friction
   (something that went wrong, was corrected, or was awkward) and for
   gaps (something that should exist as a skill but doesn't). Extract
   findings, don't reproduce: pull out the specific friction/gap signals
   into findings — don't quote large stretches of the transcript
   verbatim into the proposal output.
2. **Classify each finding into one of three buckets:**
   - **skill-update** — an existing skill's `SKILL.md` (or a reference
     file it points to) should change.
   - **new-skill** — no existing skill covers this; a new one is needed.
   - **bug-issue** — something broke and is worth tracking as a GitHub
     issue.
3. **Identify the target repository for each finding before proposing
   anything.** A skill-update or new-skill proposal targets the skill's
   actual editable source repository — **never an installed plugin's
   cache path** (for example, `~/.claude/plugins/cache/...`); an edit
   there is silently worthless, since the cache isn't the source of
   truth and gets overwritten on the next install/update. A bug-issue
   proposal targets whichever repository the friction actually belongs
   to — not necessarily this one, if the friction came from using a
   *different* installed plugin's skill.
   - **If the target repository can't be determined, or `gh`/git access
     to it isn't available, fall back to proposal-only for that item**:
     describe the change or issue content and say plainly why it can't
     be acted on, rather than guessing a repository or silently dropping
     the finding.
4. **Show concrete content before asking.** For each proposal, show the
   actual content — the real diff/edit for a skill-update or new-skill,
   the real title and body for a bug-issue — before asking whether to
   implement it now. Never ask for a yes/no on content the user hasn't
   actually seen.
5. **Per-item choice.** For each proposal: "implement now" drafts and
   applies the skill-update/new-skill (committing it via `git-flow`'s
   conventions) or files the bug-issue immediately; anything else leaves
   it recorded as a proposal in the session output, not acted on.

## Output

A grouped list of proposals (skill-update / new-skill / bug-issue), each
with its concrete content and its target repository named explicitly,
followed by whatever was actually implemented versus left as a proposal.
