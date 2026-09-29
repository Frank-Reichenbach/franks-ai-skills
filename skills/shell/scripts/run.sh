#!/usr/bin/env bash
# Wrapper for running shell commands: a best-effort secret-path check
# (blocks known secret locations unless explicitly overridden), redacts
# secret-shaped substrings from the echoed command and from stdout/stderr,
# preserves the real exit status, and bounds large output while keeping
# failure diagnostics visible. See ../SKILL.md for what this does and
# does not guarantee.
#
# Usage:
#   run.sh [--allow-secret-path] '<command>'
#
# The command is a single string, executed via `bash -c`, so any quoting
# inside it is preserved exactly as written.
#
# --allow-secret-path must come from the user, never added by the agent
# on its own initiative just because the first attempt was blocked.
#
# Non-interactive: stdout/stderr are only shown after the command
# finishes. Don't route a command that prompts for input through this
# wrapper — the prompt won't be visible until the command completes (or
# hangs waiting for input that will never arrive).

set -uo pipefail

MAX_OUTPUT_BYTES="${RUN_SH_MAX_OUTPUT_BYTES:-204800}"
# Decimal only (no leading zeros — bash's arithmetic context treats a
# leading "0" as octal, silently reinterpreting e.g. "010" as 8), and
# capped at 9 digits (max 999999999, ~954 MB) — comfortably inside
# signed 64-bit range so stdout_size + stderr_size and similar arithmetic
# below can never overflow, however this value was supplied.
if ! [[ "$MAX_OUTPUT_BYTES" =~ ^(0|[1-9][0-9]{0,8})$ ]]; then
  echo "run.sh: RUN_SH_MAX_OUTPUT_BYTES must be a decimal integer from 0 to 999999999 with no leading zeros, got '${MAX_OUTPUT_BYTES}'" >&2
  exit 2
fi

# Best-effort, not sandboxing: pattern-matches the command string for
# known secret-location shapes, bounded by non-word characters — quotes,
# redirects, and shell separators like ; & | all count as valid
# boundaries, not just whitespace, so `cat ".env"` and `cat .env; true`
# are caught the same as `cat .env`. Cannot see what a called script
# reads internally.
#
# One entry per category: a fixed label and its pattern. On a match the
# diagnostic prints only the label, never the matched text — a match can
# span secrets glued to the path (the .pem pattern extends back to the
# previous whitespace), in formats redact() doesn't know. The more
# specific .aws/credentials comes before the generic credentials entry
# so it gets its own label.
SECRET_PATH_BOUNDARY_START='(^|[^A-Za-z0-9_-])'
SECRET_PATH_BOUNDARY_END='([^A-Za-z0-9_-]|$)'
SECRET_PATH_LABELS=(
  ".env file"
  ".pem file"
  "SSH key file"
  ".ssh directory"
  "AWS credentials file"
  "credentials file"
  ".netrc file"
)
SECRET_PATH_CORES=(
  '\.env([.][A-Za-z0-9_.-]+)?'
  '[^[:space:]]*\.pem'
  'id_rsa|id_ed25519'
  '\.ssh/[A-Za-z0-9_./-]*'
  '\.aws/credentials'
  'credentials(\.json)?'
  '\.netrc'
)

# Prints the label of the first category the command matches; returns 1
# if none does. Matches bytewise (LC_ALL=C): in a UTF-8 locale an invalid
# byte anywhere in the command makes the regex match fail, which would
# let `cat .env #<invalid byte>` through unchecked.
secret_path_label() {
  local i pattern LC_ALL=C
  for i in "${!SECRET_PATH_CORES[@]}"; do
    pattern="${SECRET_PATH_BOUNDARY_START}(${SECRET_PATH_CORES[$i]})${SECRET_PATH_BOUNDARY_END}"
    if [[ "$1" =~ $pattern ]]; then
      printf '%s' "${SECRET_PATH_LABELS[$i]}"
      return 0
    fi
  done
  return 1
}

allow_secret_path=0
if [[ "${1:-}" == "--allow-secret-path" ]]; then
  allow_secret_path=1
  shift
fi

if [[ $# -ne 1 ]]; then
  echo "run.sh: usage: run.sh [--allow-secret-path] '<command>'" >&2
  exit 2
fi

cmd="$1"

if [[ "$allow_secret_path" -eq 0 ]] && matched_label=$(secret_path_label "$cmd"); then
  echo "run.sh: blocked — command appears to reference a secret location (matched: ${matched_label})." >&2
  echo "run.sh: best-effort pattern match, not a guarantee. If the user has explicitly authorized this, re-run with --allow-secret-path as the first argument." >&2
  exit 3
fi

# Matches complete values, including quoted ones and base64-shaped ones
# (+, /, = are common in tokens), not just "word" characters.
# Best-effort: an unusual format can still slip past.
#
# A key= or token= value (api_key= included) is the whole shell word
# after the =, as bash reads it: unquoted characters, backslash escapes,
# and "…", '…' and $'…' fragments, so a quoted value with spaces, \" or
# '\'' in it is masked as a whole. A value of fewer than 8 characters,
# counted as written with its quotes, stays readable. A value that ends
# its line inside an open quote, or with a backslash, continues on the
# next line: the rest of the line is masked, and so is the next line up
# to the closing quote or the end of the word. If the input ends first,
# everything after the opening quote stays masked. The hold space
# carries the open state from one line to the next: D ("), S ('),
# A ($'), C (backslash) or N (none).
#
# sed marks a value while it works on it (@RUNSH_…@); markers already in
# the input are neutralized first, so they can't unmask a value, and
# show as @RUNSH-… in the output.
q="'"
# One fragment of a shell word; a quote left open to the end of the
# line; the rest of a quote opened on an earlier line.
dq='"([^"\\]|\\.)*"'
sq="$q[^$q]*$q"
aq='\$'"$q"'([^'"$q"'\\]|\\.)*'"$q"
frag="($dq|$sq|$aq|"'\\.|[^"'"$q"'[:space:];\\])'
dq_open='"([^"\\]|\\.)*\\?$'
sq_open="$q[^$q]*\$"
aq_open='\$'"$q"'([^'"$q"'\\]|\\.)*\\?$'
bs_open='\\$'
dq_close='([^"\\]|\\.)*"'
sq_close="[^$q]*$q"
aq_close='([^'"$q"'\\]|\\.)*'"$q"
name='([Kk][Ee][Yy]|[Tt][Oo][Kk][Ee][Nn])'

redact_script=
add() { redact_script+="$1"$'\n'; }
# A value matched by $1 that continues on the next line: replace it with
# $2 and tag the line with the state the next line starts in.
continues() {
  add "s/$1$dq_open/$2@RUNSH_QD@/"
  add "s/$1$sq_open/$2@RUNSH_QS@/"
  add "s/$1$aq_open/$2@RUNSH_QA@/"
  add "s/$1$bs_open/$2@RUNSH_QC@/"
}

add 's/@RUNSH_/@RUNSH-/g'
# Prefix the line with the state the previous line left.
add 'x'
add 'G'
# A line that starts inside a value: mask up to where the value ends.
for state in D S A C; do
  case $state in
    D) close=$dq_close ;;
    S) close=$sq_close ;;
    A) close=$aq_close ;;
    C) close= ;;
  esac
  continues "^$state\\n$close$frag*" '[REDACTED]'
  add "s/^$state\\n$close$frag*/[REDACTED]/"
  [ "$state" = C ] || add "s/^$state\\n.*/[REDACTED]@RUNSH_Q$state@/"
done
add 's/^N?\n//'
# Mask one complete value at a time, leftmost first, so a name inside a
# value never counts as a name of its own. The = is marked on each
# value handled, so the loop ends.
add ':loop'
add 't loopreset'
add ':loopreset'
add "s/$name=($frag+)/\\1@RUNSH_A@\\2@RUNSH_B@/"
add 't mark'
add 'b done'
add ':mark'
continues '@RUNSH_A@.*@RUNSH_B@' '@RUNSH_M@=[REDACTED]'
add 's/@RUNSH_A@.{8,}@RUNSH_B@/@RUNSH_M@=[REDACTED]/'
add 's/@RUNSH_A@(.*)@RUNSH_B@/@RUNSH_S@=\1/'
add 'b loop'
add ':done'
# A value that opens a quote or ends in a backslash right after the =.
continues "$name=$frag*" '\1@RUNSH_M@=[REDACTED]'
add "s/[Bb]earer[[:space:]]+[\"']?[^\"'[:space:];]{8,}[\"']?/Bearer [REDACTED]/g"
add "s/sk-[^\"'[:space:];]{5,}/[REDACTED]/g"
add 's/@RUNSH_[MS]@=/=/g'
# Move the line's state tag into the hold space, N if it has none.
add 't statereset'
add ':statereset'
add 'h'
add 's/.*@RUNSH_Q(.)@$/\1/'
add 't state'
add 's/.*/N/'
add ':state'
add 'x'
add 's/@RUNSH_Q.@$//'

redact() {
  # sed's own error text (e.g. "illegal byte sequence" on invalid bytes
  # under the current locale) is suppressed here — the caller checks this
  # function's exit status and prints its own clear, attributed notice
  # instead of leaking sed's raw, unattributed error line.
  sed -E -e "$redact_script" 2>/dev/null
}

printf '$ %s\n' "$cmd" | redact

stdout_raw=$(mktemp)
stderr_raw=$(mktemp)
stdout_redacted=$(mktemp)
stderr_redacted=$(mktemp)
trap 'rm -f "$stdout_raw" "$stderr_raw" "$stdout_redacted" "$stderr_redacted"' EXIT

bash -c "$cmd" >"$stdout_raw" 2>"$stderr_raw"
status=$?

# Validate UTF-8 before attempting redaction at all — sed's behavior on
# invalid byte sequences is not portable (BSD sed on macOS errors out
# partway through; GNU sed on Linux has been observed to pass an invalid
# byte through unchanged instead of failing, which would otherwise reach
# a caller expecting valid UTF-8 text undetected). iconv's UTF-8-to-UTF-8
# round-trip is a standard, consistently-enforced validity check on both.
is_valid_utf8() {
  iconv -f UTF-8 -t UTF-8 >/dev/null 2>&1
}

# head -c/tail -c cut at raw byte offsets, which can land in the middle
# of a multibyte UTF-8 character even when the full input was valid —
# producing invalid output from valid input. Since valid UTF-8 is
# self-synchronizing, backing off at most 3 further bytes (the longest a
# character gets) from any cut point always reaches a clean boundary, so
# these never need to search further than that. Sets SAFE_TRUNC_BYTES to
# the byte count actually used, which can be less than requested.
safe_head() {
  local file="$1" n="$2" try candidate
  for try in 0 1 2 3; do
    candidate=$((n - try))
    if [[ "$candidate" -lt 0 ]]; then
      break
    fi
    if head -c "$candidate" "$file" | is_valid_utf8; then
      head -c "$candidate" "$file"
      SAFE_TRUNC_BYTES=$candidate
      return 0
    fi
  done
  SAFE_TRUNC_BYTES=0
  return 1
}

safe_tail() {
  local file="$1" n="$2" try candidate
  for try in 0 1 2 3; do
    candidate=$((n - try))
    if [[ "$candidate" -lt 0 ]]; then
      break
    fi
    if tail -c "$candidate" "$file" | is_valid_utf8; then
      tail -c "$candidate" "$file"
      SAFE_TRUNC_BYTES=$candidate
      return 0
    fi
  done
  SAFE_TRUNC_BYTES=0
  return 1
}

# Redact the COMPLETE captured content before any truncation — truncating
# first can cut a secret mid-token, shortening it below a redaction
# pattern's minimum length and leaking the (shortened) prefix.
stdout_redaction_ok=1
stderr_redaction_ok=1
if is_valid_utf8 < "$stdout_raw"; then
  redact < "$stdout_raw" > "$stdout_redacted" || stdout_redaction_ok=0
else
  stdout_redaction_ok=0
fi
if is_valid_utf8 < "$stderr_raw"; then
  redact < "$stderr_raw" > "$stderr_redacted" || stderr_redaction_ok=0
else
  stderr_redaction_ok=0
fi

# sed can also fail partway on its own (belt-and-braces alongside the
# UTF-8 check above) and still leave a partial, unverified result in the
# output file. Never show that: on failure, discard
# whatever sed did or didn't manage to write, rather than risk showing
# content that was never fully scanned for secrets.
if [[ "$stdout_redaction_ok" -eq 0 ]]; then
  : > "$stdout_redacted"
fi
if [[ "$stderr_redaction_ok" -eq 0 ]]; then
  : > "$stderr_redacted"
fi

stdout_size=$(wc -c < "$stdout_redacted" | tr -d ' ')
stderr_size=$(wc -c < "$stderr_redacted" | tr -d ' ')

if [[ "$((stdout_size + stderr_size))" -le "$MAX_OUTPUT_BYTES" ]]; then
  cat "$stdout_redacted"
  cat "$stderr_redacted" >&2
else
  # Failure diagnostics (stderr) take priority over stdout when both
  # can't fit in the budget — never silently drop the reason a command
  # failed just because it also printed a lot to stdout first.
  if [[ "$stderr_size" -ge "$MAX_OUTPUT_BYTES" ]]; then
    safe_tail "$stderr_redacted" "$MAX_OUTPUT_BYTES" >&2
    echo >&2
    echo "[run.sh: stderr truncated — ${stderr_size} bytes total, showing last ${SAFE_TRUNC_BYTES}]" >&2
    if [[ "$stdout_size" -gt 0 ]]; then
      echo "[run.sh: stdout omitted entirely (${stdout_size} bytes) to keep stderr within the ${MAX_OUTPUT_BYTES}-byte limit]"
    fi
  else
    stdout_budget=$((MAX_OUTPUT_BYTES - stderr_size))
    safe_head "$stdout_redacted" "$stdout_budget"
    echo
    echo "[run.sh: stdout truncated — ${stdout_size} bytes total, showing first ${SAFE_TRUNC_BYTES}]"
    cat "$stderr_redacted" >&2
  fi
fi

if [[ "$stdout_redaction_ok" -eq 0 ]]; then
  echo "[run.sh: stdout withheld — it is not valid UTF-8, or could not be fully redacted; shown as empty rather than risking unredacted or partially-scanned content]"
fi
if [[ "$stderr_redaction_ok" -eq 0 ]]; then
  echo "[run.sh: stderr withheld — it is not valid UTF-8, or could not be fully redacted; shown as empty rather than risking unredacted or partially-scanned content]" >&2
fi

exit "$status"
