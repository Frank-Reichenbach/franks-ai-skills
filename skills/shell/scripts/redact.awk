# redact.awk: masks key= and token= values (api_key= included) as bash
# reads them. Called by run.sh; run it with LC_ALL=C, so it works on
# bytes and a multi-byte character never matches the ASCII characters it
# looks for.
#
# A value is the whole shell word after the =: unquoted characters,
# backslash escapes, and "…", '…', $'…' and $"…" fragments. A value of
# fewer than 8 bytes, counted as written, stays readable, unless it
# continues onto another line. The name is found wherever it appears,
# also inside quotes, just as a plain text match would.
#
# Bash removes a backslash-newline before it reads names, quotes and $'.
# This scanner reads one physical line at a time and carries across the
# line break what that join needs:
#
#   st    the state of a value that continues onto the next line:
#         U  unquoted, after a backslash-newline
#         P  unquoted, a $ right before a backslash-newline, so the next
#            line's first quote may still make it $'…' or $"…"
#         D  inside "…" or $"…"
#         S  inside '…'
#         A  inside $'…'
#         "" (empty) outside any value
#   tail  outside a value, the last 5 bytes before a trailing backslash,
#         so a name split by the line break (API_KE\ + Y=) is found
#
# Every line of a value that spans lines is masked. If the input ends
# inside a value, everything after its start stays masked.
#
# nonl=1 (set by run.sh) means the input doesn't end in a newline, which
# awk can't see itself; the output then doesn't either.

BEGIN { st = ""; tail = "" }

{
    if (NR > 1) printf "\n"
    line = $0
    len = length(line)
    pos = 1
    joined = tail
    tail = ""

    # A line that starts inside a value.
    if (st != "") {
        e = value(1)
        emit(substr(line, 1, e - 1), 1)
        pos = e
    }
    if (st == "") scan()

    # A trailing backslash outside a value may join this line to the
    # next one.
    if (st == "" && substr(line, len, 1) == "\\") {
        start = len - 5
        if (start < 1) start = 1
        t = substr(line, start, len - start)
        if (len - 1 < 5) t = joined t
        tail = substr(t, length(t) > 5 ? length(t) - 4 : 1)
    }
}

END { if (NR > 0 && !nonl) printf "\n" }

# Prints the rest of the line from pos, masking every value after a
# key= or token= name. The line is split at each = once, so a line with
# many values is still read in one pass.
function scan(    n, parts, i, eq, e) {
    if (index(substr(line, pos), "=") == 0) {
        printf "%s", substr(line, pos)
        return
    }
    n = split(substr(line, pos), parts, "=")
    eq = pos - 1
    for (i = 1; i < n; i++) {
        eq += length(parts[i]) + 1
        # An = inside a value handled already is part of that value.
        if (eq < pos || !named(eq)) continue
        printf "%s", substr(line, pos, eq - pos + 1)
        pos = eq + 1
        e = value(pos)
        emit(substr(line, pos, e - pos), st != "")
        pos = e
        if (st != "") return
    }
    printf "%s", substr(line, pos)
}

# Whether the name before the = at position p ends in key or token, any
# case, with a name split by a backslash-newline joined first.
function named(p,    s) {
    if (p - 1 >= 5) s = substr(line, p - 5, 5)
    else s = joined substr(line, 1, p - 1)
    s = tolower(s)
    return s ~ /(key|token)$/
}

# Returns the position after the value that starts at i. If the value
# continues onto the next line, it returns len + 1 and sets st to the
# state the next line starts in; otherwise it clears st.
function value(i,    q, c) {
    q = (st == "" ? "U" : st)
    st = ""
    if (q == "P") {
        c = substr(line, i, 1)
        if (c == "'") { q = "A"; i++ }
        else if (c == "\"") { q = "D"; i++ }
        else if (c == "\\" && i == len) { st = "P"; return len + 1 }
        else q = "U"
    }
    while (i <= len) {
        c = substr(line, i, 1)
        if (q == "U") {
            if (c == " " || c == "\t" || c == ";" || c == "\r" || c == "\v" || c == "\f") return i
            if (c == "\\") {
                if (i == len) { st = "U"; return len + 1 }
                i += 2
                continue
            }
            if (c == "\"") q = "D"
            else if (c == "'") q = "S"
            else if (c == "$") {
                c = substr(line, i + 1, 1)
                if (c == "'") { q = "A"; i++ }
                else if (c == "\"") { q = "D"; i++ }
                else if (c == "\\" && i + 1 == len) { st = "P"; return len + 1 }
            }
            i++
        } else if (q == "S") {
            if (c == "'") q = "U"
            i++
        } else {
            # D and A: a backslash escapes the next byte; at the end of
            # the line it leaves the quote open.
            if (c == "\\") { i += 2; continue }
            if ((q == "D" && c == "\"") || (q == "A" && c == "'")) q = "U"
            i++
        }
    }
    if (q != "U") st = q
    return len + 1
}

# Prints a value, masked unless it is shorter than 8 bytes and doesn't
# continue onto or from another line (forced).
function emit(r, forced) {
    if (r == "") return
    if (!forced && length(r) < 8) printf "%s", r
    else printf "[REDACTED]"
}
