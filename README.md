# franks-ai-skills

Frank's personal AI skill collection — a Claude Code marketplace and an
[Agent Plugins 1.0](https://agent-plugins.org/) package.

## Install

**Claude Code:**

```
/plugin marketplace add Frank-Reichenbach/franks-ai-skills
/plugin install frank@franks-ai-skills
```

**Codex / other [Agent Plugins 1.0](https://agent-plugins.org/) clients:**
this repo's root `plugin.json` is a standalone, valid Agent Plugins 1.0
package on its own — `skills/` is auto-discovered per that spec, no extra
step needed if your client lets you point directly at a plugin's path or
repo.

For discovery through Codex's own marketplace UI, register this repo as a
marketplace source:

```
codex plugin marketplace add Frank-Reichenbach/franks-ai-skills
```

The ChatGPT desktop app reads `.claude-plugin/marketplace.json` as a
recognized ("legacy-compatible") marketplace format, so this repo's
existing Claude Code marketplace file doubles as the Codex catalog too —
no separate `.agents/plugins/marketplace.json` needed. From there,
installing the plugin happens in the ChatGPT desktop app's Plugins
Directory, not via a documented single-plugin CLI command; see
[Codex's plugin docs](https://developers.openai.com/codex/plugins/build)
for anything that's changed since.

## Skills

- `skill-writing` — authoring and reviewing `SKILL.md` files, and this
  repo's marketplace/plugin/eval conventions.
- `r00t` — this plugin's entry point; establishes a session-wide
  routing convention to the rest of the skills below.
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

See `skills/skill-writing/SKILL.md` for how to add another.

## Structure

- `skills/<name>/SKILL.md` — canonical source for every skill.
- `.claude-plugin/marketplace.json` — Claude Code marketplace and the `frank` plugin entry.
- `plugin.json` — Agent Plugins 1.0 manifest.
- `evals/<name>/` — routing and behavioral test cases per skill.
- `docs/` — repo-wide policy (security, releases, portability).
- `tools/` — `checks.py`, the structural validator, plus `validate.sh` and `requirements.txt`.
- `tools/tests/` — `checks.py`'s own unit test suite, plus the separate executable tests for `shell`'s `scripts/run.sh`.

## Validate

Prerequisites: `python3`, the packages in `tools/requirements.txt`
(`pip install -r tools/requirements.txt`), and the `claude` CLI.

```
./tools/validate.sh
```

Runs on every pull request via `.github/workflows/validate.yml`, in three
steps: the unit test suite (`python3 -m unittest discover -s tools/tests`),
then `claude plugin validate . --strict` (hence the `claude` CLI
prerequisite), then the structural checks (`python3 tools/checks.py`).
