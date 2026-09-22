---
name: skill-writing
description: Guides authoring and reviewing SKILL.md files, and explains how this repo's marketplace, plugin, and eval conventions work. Use when creating a new skill, editing an existing skill, deciding whether a change needs a new plugin entry, or adding eval cases for a skill.
---

# Skill Writing

## Naming

- Directory name and frontmatter `name` must match exactly.
- Lowercase letters, numbers, hyphens only. Max 64 characters.
- Never `anthropic`, `claude`, or any reserved word as the whole name.
- Prefer a capability-oriented name (`skill-writing`, `security-review`) over a vague or organizational one (`helper`, `engineering`, `utils`).

## Writing the description

`description` is a classifier, not marketing copy. An agent sees only `name` and `description` for every skill before deciding whether to load the rest — get this wrong and the skill never triggers, or triggers on the wrong prompts.

- Third person only ("Extracts...", never "I can help..." or "You can use this to...").
- State both what the skill does and when to use it.
- Include concrete trigger terms a user would actually type.
- Max 1024 characters, no XML tags, non-empty.

Bad: `description: Helps with skills.`
Good: `description: Reviews proposed software architectures for component boundaries, failure modes, and tradeoffs. Use when evaluating an architecture, ADR, or system decomposition.`

## What a skill's body should contain

A skill is procedural knowledge, not a topic overview. Beyond naming and
description, the body should give the agent:

- **Purpose and scope**: what this skill covers, and — as importantly —
  what it doesn't, so it isn't invoked outside its boundary.
- **Procedure**: the actual steps, in order, especially any that aren't
  obvious from general capability. Don't restate what a capable model
  already knows ("be thorough," "write clean code") — encode the
  non-obvious constraint or sequence that would otherwise get relearned by
  trial and error.
- **Decision points**: where the procedure branches, and what signal
  decides each branch. In this repo, "new skill vs. new plugin" is exactly
  this kind of decision point (see "When to add a new plugin instead of
  adding to `frank`" above) — a skill with a judgment call should spell
  out the question to ask, not just the two possible answers.
- **Quality criteria**: what makes the output good, stated concretely
  enough to self-check against — not "be helpful," but "the description
  names both what the skill does and when to use it."
- **Failure/stop conditions**: when to stop and ask rather than guess, and
  what "this request doesn't fit this skill" looks like.
- **Expected output**: the shape of what the skill produces, so both the
  agent and a reviewer can tell when it's done.

A skill missing these can still pass every mechanical check in this repo —
frontmatter valid, files created, `tools/validate.sh` green — while giving
an agent no real guidance: formally correct, practically useless. The
checks in this repo verify format; they cannot verify that the procedure
inside is actually good. That judgment is the author's, and it's the part
worth spending the most effort on.

## Progressive disclosure

Keep `SKILL.md` itself under roughly 500 lines. If it grows past that, split detail into reference files linked directly from `SKILL.md` — never nested more than one level deep (a file `SKILL.md` links to should not itself link to a third file for the same topic; an agent may only partially read files reached through a second hop).

## Vendor-neutral wording

This repo ships skill content to more than one client (Claude Code via `.claude-plugin/marketplace.json`, and any Agent Plugins 1.0 client such as Codex via the root `plugin.json`). Write skill bodies so they work unmodified in both:

- Prefer "the agent's available web-search capability" over "Claude's WebSearch tool."
- Prefer "the agent's subagent/sub-task mechanism" over "a Claude subagent."
- Only name Claude Code explicitly when the instruction is genuinely Claude-Code-specific (for example, a reference to `~/.claude/skills`).

## This repo's structure

Everything above (naming, description, body content, progressive
disclosure, vendor-neutral wording) applies to any skill, anywhere. This
section and "Evals" below are specific to contributing a skill *to the
franks-ai-skills repository itself* — if this skill triggers while you're
authoring a skill for a different project, apply the guidance above but
skip the `marketplace.json` and eval-file steps below unless that project
has its own equivalent conventions.

```
franks-ai-skills/
├── plugin.json                  # Agent Plugins 1.0 manifest (Codex, etc.)
├── .claude-plugin/
│   └── marketplace.json         # Claude Code marketplace + the "frank" plugin entry
├── skills/<name>/SKILL.md       # canonical source for every skill
├── evals/<name>/{routing,behavior}.yaml
└── evals/catalog/collisions.yaml
```

- **Skill vs. plugin vs. marketplace**: a skill is one directory under `skills/`. The `frank` plugin is *virtual* — it is defined entirely inside `.claude-plugin/marketplace.json` (`"source": "./"`, `"strict": false`, an explicit `"skills"` array). There is no `plugins/frank/` folder and no per-plugin `plugin.json`; adding a skill to the plugin is a one-line edit to that `skills` array, not a file move.
- **Adding a new skill**: create `skills/<name>/SKILL.md`, add its path to the `frank` entry's `skills` array in `.claude-plugin/marketplace.json`, and add `evals/<name>/routing.yaml` + `evals/<name>/behavior.yaml` (see below).
- **When to add a new plugin instead of adding to `frank`**: only when a real boundary appears — different install audience, a skill that needs different trust/permissions (for example, it runs scripts with network access), a different dependency footprint, or a different release cadence. Not for topic/taxonomy reasons alone.

## Evals

Every skill gets two required files under `evals/<name>/`:

- `routing.yaml` — prompts that should and should not trigger this skill.
- `behavior.yaml` — once triggered, what the skill should actually do.

These are checked for structure by `tools/validate.sh` (required top-level keys present) but are not yet executed against a live model in CI — see `docs/releases.md` for why, and `evals/catalog/collisions.yaml` for the cross-skill routing check that becomes useful once a second skill exists.

A skill with any real decision points (see above) should also add one or
more `evals/<name>/behavior-<scenario>.yaml` files — same `prompt`/`expect`
shape as `behavior.yaml`, one file per judgment-heavy scenario. These are
supplementary: not required, not yet checked by `tools/checks.py`, but
they're what makes a decision point verifiable instead of just described.
`evals/skill-writing/behavior-plugin-boundary.yaml` and
`evals/skill-writing/behavior-ambiguous-request.yaml` are the examples for
this skill.

## Policy that lives outside this skill

- `docs/security.md` — rules for skills that bundle scripts.
- `docs/releases.md` — versioning approach.
- `docs/portability.md` — why two manifests exist.
