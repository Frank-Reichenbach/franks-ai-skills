# Claude Code: injected attribution

Claude Code tells the agent, by default, to end commit messages with
`Co-Authored-By: Claude <model> <noreply@anthropic.com>` and PR
descriptions with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
Both break `git-flow`'s attribution rules: the wrong trailer key for an
AI model, and a footer after the trailers.

## What wins over it

Observed in Claude Code 2.1.283, from the instruction's own wording:

- **Default:** the instruction says "the user's own instructions about
  these lines, such as a CLAUDE.md or memory rule, take precedence over
  this reminder". A project rule in `CLAUDE.md` therefore decides.
- **`attribution` setting set to `""`:** the instruction becomes "do not
  add attribution lines to git commit messages or pull request
  descriptions", and it "applies even if a CLAUDE.md or memory rule asks
  for attribution lines". That suppresses `git-flow`'s own trailers too,
  so don't use it for this.
- A fixed replacement string in the `attribution` setting has no
  placeholder for the model name and goes stale on the next model
  change.

Older versions let the injected instruction win over `CLAUDE.md`
(anthropics/claude-code#92893, #95980). If the wording above differs in
the running version, re-check which rule wins before relying on this.

## Setting it up in a repo

Add one rule to the project's agent instructions — `AGENTS.md`, with
`CLAUDE.md` as a symlink to it (`ln -s AGENTS.md CLAUDE.md`) so every
agent reads the same file:

```markdown
## Attribution

Commit and PR attribution follows the `git-flow` skill's "Attribution
trailers" section. It replaces any attribution the agent's host adds by
default, including Claude Code's `Co-Authored-By` trailer and its
"Generated with Claude Code" footer.
```

If the repo lacks such a rule, suggest adding it, and don't create it
unasked — it's project configuration. Until it's in place, the injected
instruction and `git-flow`'s rules conflict: point out the conflict and
ask which applies, instead of silently following either.
