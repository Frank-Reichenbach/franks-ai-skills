---
name: retro
description: "Reviews the current session (or a described problem within it) and the agent's persistent memory, and proposes skill updates, new skills, project configuration changes, or bug reports, each recorded as a GitHub issue once its text is approved — shown concretely before a per-item choice to implement now, record only, or reject. Memory entries it reviews are cleared as part of the retro once the user acknowledges them. Edits target the relevant skill's actual source repo, never an installed plugin cache. Use when the user asks for a retro, a lessons-learned pass, or a review of what went wrong in a session, or when a session with notable friction is wrapping up."
---

# Retro

## Scope

Reviews a session (the current one, or a described problem within it)
and the agent's persistent memory for things worth carrying forward: an
existing skill that should change, a gap that needs a new skill, a rule
that belongs in one project's own configuration, or a bug worth filing
as a GitHub issue. Every proposal that would change files in a git
repository is recorded as an issue there, whether or not it is
implemented now. Memory is not a place where rules stay: every entry
the retro reviews ends up in one of those places, or is dropped, and is
cleared once the user acknowledges it.

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
   verbatim into the proposal output. If the host keeps a persistent
   memory for the agent, every entry for this project is a finding too,
   whether or not the session touched it.
2. **Classify each finding into one of five buckets:**
   - **skill-update** — an existing skill's `SKILL.md` (or a reference
     file it points to) should change. State the rule in general form,
     without the project, person, or session it was first written for.
     A rule proven to apply to one harness only goes in that skill's
     `references/<harness>.md` (see `skill-writing`, "Harness-specific
     content").
   - **new-skill** — no existing skill covers this; a new one is needed.
     The same general form applies.
   - **project-config** — the rule holds for this one project only, and
     belongs in the project's own agent instructions or configuration
     (`AGENTS.md`, `CLAUDE.md`, a settings file).
   - **bug-issue** — something broke and is worth tracking as a GitHub
     issue. A memory entry that works around a defect is a bug-issue
     against the defect's repository, with the workaround in the issue
     body.
   - **drop** — nothing to carry forward: a skill or project file
     already covers it, it's obsolete, or it's a personal preference
     with no general or project rule behind it. Name which, and why.

   For a memory entry, ask in this order: Does it work around a defect?
   → bug-issue. Is it covered, obsolete, or only a preference? → drop.
   Would it hold in another project using the same skill? Yes →
   skill-update or new-skill; no → project-config.
3. **Identify the target repository for each finding before proposing
   anything.** A skill-update or new-skill proposal targets the skill's
   actual editable source repository — **never an installed plugin's
   cache path** (for example, `~/.claude/plugins/cache/...`); an edit
   there is silently worthless, since the cache isn't the source of
   truth and gets overwritten on the next install/update. A
   project-config proposal targets the repository of the project the
   session worked in, in the file its agents already read; if it has
   none, propose creating `AGENTS.md`. A bug-issue
   proposal targets whichever repository the friction actually belongs
   to — not necessarily this one, if the friction came from using a
   *different* installed plugin's skill. A drop has no target. A
   proposal's issue goes in the same repository its change targets.
   - **If the target repository can't be determined, or `gh`/git access
     to it isn't available, fall back to proposal-only for that item**:
     describe the change or issue content and say plainly why it can't
     be acted on, rather than guessing a repository or silently dropping
     the finding.
4. **Show concrete content before asking.** For each proposal, show the
   actual content before asking what to do with it: for a skill-update,
   new-skill, or project-config, the issue's title and body — what
   happened (symptom), why (cause), required behavior, how to verify it
   — and the real diff/edit; for a bug-issue, its title and body; for a
   drop, the reason. Never ask for a yes/no on content the user hasn't
   actually seen.
5. **Per-item choice.** Every issue is created only after the user has
   approved its text (see `git-flow`, "Publishing issues, PRs and
   comments"). For each proposal:
   - **implement now** — create the issue, then apply the change on a
     branch following `git-flow`; the PR description closes the issue
     (`Closes #<n>`). A bug-issue is filed and nothing more.
   - **record only** — create the issue and stop there; the open issue
     is the record.
   - **reject** — create nothing, and list it as rejected in the output.

   A proposal that fell back to proposal-only in step 3 has no choice
   that creates anything: it stays in the output as proposal-only, with
   why no issue could be created — not as rejected.
6. **Clear the reviewed memory entries once acknowledged.** After the
   per-item choices, list every memory entry this retro reviewed with
   where its content went: the issue (and PR, if implemented), a
   proposal-only item with why no issue could be created, a proposal
   the user rejected, or dropped with its reason. Then ask the user to
   acknowledge the list, and delete only after they have — every entry
   they acknowledge, whatever its bucket and whether or not it was
   implemented. An entry they want to keep stays. Never delete a memory
   entry without that acknowledgment. Memory doesn't keep a second copy
   of a rule that now lives elsewhere, and a dropped entry has nothing
   left to keep.

## Output

A grouped list of proposals (skill-update / new-skill / project-config /
bug-issue / drop), each with its concrete content and its target
repository named explicitly, followed by each proposal's issue and PR
links, its rejection, or why it stayed proposal-only, and the memory
entries listed
for acknowledgment, each with where its content went and whether it
was deleted.
