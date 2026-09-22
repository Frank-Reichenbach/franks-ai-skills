# Releases

This repo currently is one plugin (`frank`), so it gets one version:

- `plugin.json` (`version`) and the `frank` entry in `.claude-plugin/marketplace.json` (`version`) are bumped together.
- Tag the repo itself, e.g. `v0.1.0`, `v0.2.0`.
- No per-skill versioning. Git history is a skill's version history.

Once a second plugin exists, each distributable plugin gets its own SemVer instead of one repo-wide version. Introduce per-skill versioning only if a specific skill becomes an independently published artifact outside this repo.

## CI

`.github/workflows/validate.yml` runs `tools/validate.sh` on every pull request: the `tools/tests` unit test suite, `claude plugin validate . --strict`, a structural check on `plugin.json` and `.claude-plugin/marketplace.json` (name/version/description shape, `license`/`repository`/`owner.url` shape if present, `strict`/`skills` field types, and that the two manifests agree on version and on the set of skills), a frontmatter lint on every `SKILL.md`, and a structural check on `evals/<skill>/routing.yaml` and `evals/<skill>/behavior.yaml` for every skill under `skills/`, plus `evals/catalog/collisions.yaml`. These are deterministic and free — no API key required.

Both `SKILL.md` frontmatter and the eval files are parsed with a real YAML parser (PyYAML — see `tools/requirements.txt`), not hand-rolled pattern matching. An earlier version tried to get away with regex-based parsing to avoid the dependency; two rounds of review found real, reproducible gaps in it (block scalars, null literals, and comments all had cases that either passed invalid content or rejected valid content), which is exactly the class of bug a real parser doesn't have. Genuinely malformed YAML in either a `SKILL.md`'s frontmatter or an eval file is now rejected, not silently accepted.

A skill's optional `evals/<skill>/behavior-<scenario>.yaml` files (for judgment-heavy decision points — see `skills/skill-writing/SKILL.md`) are **not** part of this checked set yet; they exist for a human or agent to read directly, not for `tools/checks.py` to validate.

Behavioral evaluation (actually running `evals/<name>/routing.yaml` and `behavior.yaml` against a live model, for example via `anthropics/claude-code-action`) is intentionally not wired up yet. It needs an `ANTHROPIC_API_KEY` repository secret and has a real per-run cost; add it as a separate change when that trade-off is worth making.
