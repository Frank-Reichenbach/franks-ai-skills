---
name: shell
description: "Provides a wrapper script (scripts/run.sh) for running shell commands with best-effort secret redaction (of both the command line and its output) and predictable handling of quoting, exit status, and large output. The agent judges whether a command is read-only and routes it accordingly, requiring authorization (respecting the host's own permission memory) for anything else. Use whenever a shell command needs to be run in this context."
---

# Shell

## Scope

Applies whenever a shell command needs to run in a project that has this
plugin installed. Route commands through `scripts/run.sh` rather than
calling the host's shell tool directly, for the redaction and predictable
output/exit-status handling it provides — not because it enforces
anything the host doesn't already enforce (it doesn't; see "Limits"
below).

Not for deciding what command to run, nor for the wording and voice of
prose written about a result — `git-flow` and `technical-writing`
(among others) make those calls; `shell` just executes what's already
been decided. How *much* of a result to relay is a separate question,
about context rather than wording, and this skill does answer it — see
"Limits."

## How to invoke it

```
"${CLAUDE_PLUGIN_ROOT}/skills/shell/scripts/run.sh" [--allow-secret-path] '<command>'
```

Pass the entire command as a single quoted string — the script runs it
via `bash -c`, so whatever quoting is inside that string is preserved
exactly as written. `${CLAUDE_PLUGIN_ROOT}` is Claude Code's environment
variable for resolving a path relative to the installed plugin, not the
consuming project's working directory; a bare relative `scripts/run.sh`
would resolve against the wrong directory. Other hosts' equivalent is
unverified — document it here once confirmed rather than assuming it
matches Claude Code's. **Quote `"${CLAUDE_PLUGIN_ROOT}/..."` itself, as
shown above** — left unquoted, a plugin installed under a path
containing a space breaks into multiple words and fails with "command
not found."

Requires `bash`, `sed`, and `iconv` — all present by default on macOS
and the Linux CI images this plugin has been tested against (per
`docs/security.md`'s rule to document required external binaries). No
network access is needed.

## Read-only vs. everything else

Judge this yourself — there's no fixed allowlist. If a command is
genuinely read-only (inspecting state, not changing it), run it through
the wrapper directly. For anything else, get authorization first —
through whatever the host's own permission system already provides (for
example, Claude Code's own tool-approval prompt, which already remembers
a prior "always allow" for a matching command; don't demand a fresh
prompt for something already authorized). The wrapper does not itself
gate this — see "Limits."

## What the wrapper does

1. **Secret-path check.** Before running anything, it checks the command
   string against a best-effort list of known secret-location patterns
   (`.env`, `*.pem`, `id_rsa`/`id_ed25519`, `.ssh/*`, common credentials
   file names). On a match, it refuses to run and exits non-zero,
   printing only the kind of location that matched (for example
   `.pem file`) — never the matched text, which can include a secret
   glued to the path.
2. **User-authorized override only.** On a block, the procedure is:
   explain what was blocked and why (which kind of location matched),
   then ask the user whether to proceed — and wait for their answer.
   Only after the user has actually said yes, re-invoke with
   `--allow-secret-path` as the first argument. **This override comes
   from the user, never from the agent on its own initiative** —
   retrying with the flag the moment a command is blocked, without the
   user actually authorizing it, defeats the check entirely. The flag is
   proof the check should be skipped for *this* invocation, nothing more
   — the script only checks for the flag's presence, not that a human
   actually approved it, so supplying it without real authorization is
   the agent defeating its own safety check, not a system enforcing
   anything. If the user has already authorized this specific access
   earlier in the session, that authorization holds — don't re-ask for
   the same access. Don't route around a block by reaching for a
   different command or tool to reach the same file instead.
3. **Redacted echo.** Once past the check, it prints the command it's
   about to run, with secret-shaped substrings (bearer tokens, `sk-`
   style API keys, `key=`/`token=` values) masked in that echo — not
   just in the output.
4. **Execution.** Runs the command via `bash -c`, preserving quoting and
   the real exit status.
5. **Redacted, bounded output.** stdout and stderr are captured
   separately, each fully scanned for the same secret-shaped patterns
   and masked *before* any truncation — truncating first could cut a
   secret mid-token and leak a shortened prefix. The size limit (default
   200 KB, override via `RUN_SH_MAX_OUTPUT_BYTES`) bounds only the
   combined *redacted* stdout+stderr that gets displayed — not the
   echoed command line, not the wrapper's own notices, and not how much
   a command can write to the temporary files it's captured into while
   running (a command that produces gigabytes of output before finishing
   will fill disk accordingly; the limit only governs what's shown
   afterward). Output past the limit is truncated with an explicit
   marker rather than silently cut off — at a UTF-8 character boundary,
   never mid-character, backing off a few bytes further than the limit
   allows if the cut point would otherwise split one — and stderr takes
   priority over stdout when both can't fit — a failing command's
   diagnostics are never pushed out of the visible window by a large
   stdout. A failing command's exit status and stderr are always
   surfaced, never swallowed. If a captured stream can't be safely
   redacted at all (for example, it contains a byte sequence invalid
   under the current locale), that stream is withheld entirely and
   reported as such,
   rather than shown partially processed or unprocessed.

## Limits (read this before trusting it more than you should)

- The secret-path check and the redaction are **pattern matching, not
  sandboxing**. The secret-path check inspects only the command string,
  before anything runs — it cannot see what a script the command *calls*
  does at runtime, whether that's reading a credential file or printing
  one. Redaction, by contrast, does scan everything actually captured on
  stdout/stderr, including output printed by a script the command calls
  — but it's still pattern matching, not comprehension, and can be
  fooled by a value shaped differently than the patterns expect, or miss
  a secret a called script reads but never prints.
- Masking the wrapper's *echoed* command does not remove a secret
  already present in the actual tool-call arguments the host recorded —
  by the time the wrapper runs, the agent already had to type the full
  command, secret included, to invoke it. Redaction here stops the
  secret from being *repeated* in what the wrapper prints back; it does
  not undo it having been submitted once. Prefer environment variables
  already present in the shell, a secrets file piped as input, or a
  secret-manager lookup over passing a literal secret as a command
  argument in the first place.
- Nothing in this skill stops the agent from calling the host's shell
  tool directly instead of this wrapper. This is agent guidance, not an
  enforced boundary — real enforcement, if ever wanted, is a separate,
  host-level mechanism, deliberately out of scope here.
- **Non-interactive only.** stdout/stderr are captured and only shown
  after the command finishes, so a command that prompts for input (for
  example, an interactive `read`) will appear to hang — its prompt is
  buffered and invisible until the command completes, which it won't if
  it's waiting on input that will never arrive. Don't route an
  interactive command through this wrapper.
- The output bound (`RUN_SH_MAX_OUTPUT_BYTES`, default 200 KB) exists to
  keep the conversation's own context clean, not just to cap a runaway
  command. When relaying a command's result, summarize what it means
  rather than pasting the full output back — even output that's already
  within the limit — unless the raw text is what the result is being
  used to *prove* (an error message, a diff, the evidence behind a
  review finding), or is what was asked for.
