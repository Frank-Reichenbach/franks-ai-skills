---
name: skill-writing
description: Guides authoring and reviewing SKILL.md files, and explains how this repo's marketplace, plugin, and eval conventions work. Use when creating a new skill, editing an existing skill, deciding whether a change needs a new plugin entry, or adding eval cases for a skill.
---

# Skill Writing

## Scope

Governs how to author or review a skill's own `SKILL.md` (and its
`references/*.md`, `scripts/`, evals) — naming, description, structure,
progressive disclosure, cross-skill boundaries. Not for the prose quality
of content outside a skill's own authoring conventions — see
`technical-writing` for that. Not for the commit/PR that adds or changes
a skill — see `git-flow` for that; this skill decides what the content
should say, `git-flow` decides how to commit and land it.

Stop and ask rather than guessing when: it's unclear whether a change
is an edit to an existing skill, a new skill, or a new plugin entry
(see "When to add a new plugin instead of adding to `frank`" below); a
proposed boundary would change what *another* skill owns and that
skill's own file disagrees; or a skill's purpose can't be stated as one
classifier sentence, which usually means it's two skills.

When editing an existing skill, start with that skill's own files, then
pull in what the change actually needs — its tests, which may live
outside the skill directory and go unreferenced from it (`shell`'s are
in `tools/tests/`); a dependency it relies on; or an adjacent skill
whose boundary this change touches, since a boundary has to stay true
from both sides. Deliberately, as needed — not a blanket read of every
skill in the repo.

## Naming

- Directory name and frontmatter `name` must match exactly.
- Lowercase letters, numbers, hyphens only. Max 64 characters.
- Never `anthropic`, `claude`, or another reserved word *anywhere* in the name — not as the whole name, and not as a part of one (`claude-tools`, `anthropic-helper` are both out).
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
- **Context discipline**: what this skill's own execution shouldn't
  reproduce wholesale — the specific thing to extract, summarize, or
  load only the relevant slice of, tailored to what actually risks
  bloating context when *this* skill runs (a large session transcript,
  a long document, a big command output, an unrelated part of the
  repo). This is different from the file-size discipline in "Progressive
  disclosure and context" below, which is about `SKILL.md` itself, not
  about what the skill does once it's running.

A skill missing these can still pass every mechanical check in this repo —
frontmatter valid, files created, `tools/validate.sh` green — while giving
an agent no real guidance: formally correct, practically useless. The
checks in this repo verify format; they cannot verify that the procedure
inside is actually good. That judgment is the author's, and it's the part
worth spending the most effort on.

## Cross-skill boundaries

When a skill's purpose could plausibly overlap with another skill's, say
so explicitly in the body — not just in `evals/catalog/collisions.yaml`.
Two shapes:

- **Exclusion**: "Not for X — see `other-skill` for that." Use when the
  two skills would otherwise compete for the same request and only one
  should actually handle it (`technical-writing` excludes authoring a
  skill's own `SKILL.md`; `skill-writing` excludes general prose
  elsewhere and the commit/PR that lands a change).
- **Cooperation**: "X decides what; Y decides how it's phrased, committed,
  or executed." Use when both genuinely apply to the same request at
  once, not competing (`git-flow` decides a commit's format,
  `technical-writing` decides its wording; `shell` executes what
  `git-flow` and `technical-writing` decided).

Name only skills that ship in this plugin. For a skill outside it,
describe the excluded scope instead ("Not for PDF files") — that skill
may not be installed, and the agent picks whatever fits.

When a skill realizes mid-task that a different skill fits better, name
that specific skill and invoke it directly — don't route back through
`r00t`. `r00t` establishes the session-wide routing convention once, at
the start; it isn't a dispatcher other skills call into.

Every skill in this plugin stays reachable by the agent and by other
skills. Don't set `disable-model-invocation: true`: in Claude Code it
removes the skill's description from the model's context entirely, so
only the user can invoke it and no other skill can reach it (Claude Code
skills documentation, "Control who invokes a skill"). A skill that fits
only in specific situations says so in its description's "Use when"
clause.

## Progressive disclosure and context

The context window is shared with everything else the agent needs —
every token in `SKILL.md` competes with conversation history once
loaded. Default assumption: the agent is already capable. Before adding
a sentence, ask "does the agent really need this, or does it already
know it?" — cut what doesn't earn its cost.

- Keep `SKILL.md` itself under roughly 500 lines. If it grows past that,
  split detail into reference files linked directly from `SKILL.md` —
  never nested more than one level deep (a file `SKILL.md` links to
  should not itself link to a third file for the same topic; an agent
  may only partially read files reached through a second hop).
- A reference file longer than ~100 lines gets a table of contents at
  the top, so a partial read still shows the full scope of what's there.
- Bundled reference files, scripts, and assets cost nothing until
  actually read or run — bundle comprehensive material freely; the
  discipline is about what's *always* loaded (`SKILL.md` itself), not
  what exists in the directory.
- Use one term for one concept throughout a skill, and don't switch
  partway through (pick "endpoint," not a mix of "endpoint," "route,"
  and "URL" for the same thing).

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
- **Adding a new skill**: create `skills/<name>/SKILL.md`, add its path to the `frank` entry's `skills` array in `.claude-plugin/marketplace.json`, and add `evals/<name>/routing.yaml` + `evals/<name>/behavior.yaml` (see below). Committing and opening the PR for this follows `git-flow`'s conventions, the same as any other change.
- **When to add a new plugin instead of adding to `frank`**: only when a real boundary appears — different install audience, a skill that needs different trust/permissions (for example, it runs scripts with network access), a different dependency footprint, or a different release cadence. Not for topic/taxonomy reasons alone.

## Evals

Every skill gets two required files under `evals/<name>/`:

- `routing.yaml` — prompts that should and should not trigger this skill.
- `behavior.yaml` — once triggered, what the skill should actually do.

These are checked for structure by `tools/validate.sh` (required top-level keys present, every `expect` item a string, every `cases` entry a mapping with a string `prompt`) but are not yet executed against a live model in CI — see `docs/releases.md` for why, and `evals/catalog/collisions.yaml` for the cross-skill routing check that becomes useful once a second skill exists.

A skill with any real decision points (see above) should also add one or
more `evals/<name>/behavior-<scenario>.yaml` files — same `prompt`/`expect`
shape as `behavior.yaml`, one file per judgment-heavy scenario. These are
supplementary: not required, but checked for the same structure as
`behavior.yaml` when present, and they're what makes a decision point
verifiable instead of just described.
`evals/skill-writing/behavior-plugin-boundary.yaml` and
`evals/skill-writing/behavior-ambiguous-request.yaml` are the examples for
this skill.

## Output

- **New or edited skill:** a `SKILL.md` whose body covers every element
  of the checklist in "What a skill's body should contain". In this
  repo, also the `marketplace.json` entry, `routing.yaml` and
  `behavior.yaml`, a `behavior-<scenario>.yaml` per decision point, and
  a passing `tools/validate.sh`.
- **Review:** findings against that checklist and the rules above, each
  naming the line it concerns.

## Policy that lives outside this skill

- `docs/security.md` — rules for skills that bundle scripts.
- `docs/releases.md` — versioning approach.
- `docs/portability.md` — why two manifests exist.
