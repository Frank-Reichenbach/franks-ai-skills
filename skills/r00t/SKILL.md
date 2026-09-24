---
name: r00t
description: Establishes, for the rest of the session, that this plugin's own installed skills should be considered against every request and invoked when they apply. Use at the start of every session in a project that has this plugin installed, before the first task, so later requests get routed to this plugin's skills.
---

# r00t

## Purpose

`r00t` is this plugin's entry point. Invoking it establishes a
**session-wide convention**, not a one-off lookup: from this point on in
the session, check whether one of this plugin's own skills applies to each
request, and invoke it when it does. This applies to every request for the
rest of the session — not only the one `r00t` was invoked alongside.

## Skills this plugin currently ships

- `skill-writing` — authoring and reviewing `SKILL.md` files, and this
  repo's marketplace/plugin/eval conventions.
- `technical-writing` — clarity, structure, and tone for technical prose,
  without editorializing, with a default client-facing voice projects can
  override.
- `git-flow` — branching, commit, and pull-request conventions, including
  the rule that merging always needs an explicit request or human
  approval.
- `shell` — runs shell commands through a wrapper with best-effort secret
  redaction and a user-authorized-only override for known secret
  locations.
- `retro` — reviews a session and proposes skill updates, new skills, or
  bug reports, targeting each proposal's actual source repository.

Update this list whenever a new skill is added to this plugin (see
`skills/skill-writing/SKILL.md` for how skills get added).

## Behavior

- If invoked with no task attached, acknowledge the convention (for
  example: "Got it — I'll check this plugin's skills against what you ask
  from here on") and wait for the next request. Don't do nothing, and don't
  demand a task in the same turn.
- Repeat invocation within a session is harmless — there is no
  one-time-only state to corrupt or duplicate.
- When no plugin skill fits a request, handle it normally. `r00t` never
  forces a skill onto a request it doesn't fit.
- `r00t` may note that other installed skills exist (for example,
  another plugin's own routing skill) and defer to them, but it does not
  recursively re-invoke itself, and does not hand off to another router
  in a way that could call back into `r00t`.
- No forced startup commands or context-gathering pass. `r00t` only
  routes; it does not run `git status`, read files, or otherwise probe the
  project on its own.
- `r00t` operates on whatever project has this plugin installed — not on
  the `franks-ai-skills` repository itself. Explicit project instructions
  and explicit user preferences always take precedence over any skill this
  plugin routes to.
