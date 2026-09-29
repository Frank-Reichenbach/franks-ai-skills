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

# FS = "\n" keeps each record a single field: this script never uses
# fields, and BSD awk splitting a long line at every blank took about
# 90 bytes of memory per byte of the line.
BEGIN { FS = "\n"; st = ""; tail = "" }

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
        emit(1, e, 1)
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
# key= or token= name. The line is cut into 64 KB chunks, and each chunk
# is split at each = once; the text between them is printed and checked
# from those pieces. BSD awk's substr() takes longer the longer the
# string it cuts from, so calling it on the whole line once per value
# made the time grow with the square of the number of values, and
# splitting the whole line at once made memory grow with it. A value or
# name that crosses into the next chunk is read by position, through
# at() and named().
function scan(    cstart, chunk, clen, n, parts, i, start, eq, e) {
    if (index(substr(line, pos), "=") == 0) {
        printf "%s", substr(line, pos)
        return
    }
    cstart = pos
    while (cstart <= len) {
        chunk = substr(line, cstart, 65536)
        clen = length(chunk)
        n = split(chunk, parts, "=")
        start = cstart
        for (i = 1; i < n; i++) {
            # parts[i] starts at start, and the = after it is at eq. An
            # = inside a value handled already is part of that value.
            eq = start + length(parts[i])
            if (eq >= pos) {
                printf "%s=", substr(parts[i], pos - start + 1)
                pos = eq + 1
                if (named(parts, i, cstart)) {
                    e = value(pos)
                    emit(pos, e, st != "")
                    pos = e
                    if (st != "") return
                }
            }
            start = eq + 1
        }
        # parts[n] runs to the end of the chunk, unless a value went on.
        if (pos < cstart + clen) {
            printf "%s", substr(parts[n], pos - start + 1)
            pos = cstart + clen
        }
        cstart = pos
    }
}

# Whether the name before the = after parts[i] ends in key or token, any
# case. Its last 5 bytes come from parts[i], from the pieces before it
# if it is shorter, and then from the line before the chunk that starts
# at from, or, at the start of the line, from the line before a
# backslash-newline (joined).
function named(parts, i, from,    s, j) {
    s = parts[i]
    for (j = i - 1; length(s) < 5 && j >= 1; j--) s = parts[j] "=" s
    if (length(s) < 5) {
        if (from > 5) s = substr(line, from - 5, 5) s
        else if (from > 1) s = substr(line, 1, from - 1) s
        else s = joined s
    }
    if (length(s) > 5) s = substr(s, length(s) - 4)
    return tolower(s) ~ /(key|token)$/
}

# Returns the position after the value that starts at i. If the value
# continues onto the next line, it returns len + 1 and sets st to the
# state the next line starts in; otherwise it clears st.
function value(i,    q, c) {
    q = (st == "" ? "U" : st)
    st = ""
    if (q == "P") {
        c = at(i)
        if (c == "'") { q = "A"; i++ }
        else if (c == "\"") { q = "D"; i++ }
        else if (c == "\\" && i == len) { st = "P"; return len + 1 }
        else q = "U"
    }
    while (i <= len) {
        c = at(i)
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
                c = at(i + 1)
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

# The byte at position i of the line. BSD awk's substr() takes longer
# the longer the string it cuts from, so reading a long line one byte at
# a time with it took time growing with the square of the line length.
# On a line over 1 KB, bytes are read from a 256-byte window, cut from a
# 64 KB window, cut from the line: each substr() works on a short string,
# and memory stays the same however long the line is.
function at(i) {
    if (len <= 1024) return substr(line, i, 1)
    if (w1nr != NR || i < w1 || i >= w1 + 65536) {
        w1nr = NR
        w1 = i
        win1 = substr(line, i, 65536)
        w2 = -1
    }
    if (w2 < 0 || i < w2 || i >= w2 + 256) {
        w2 = i
        win2 = substr(win1, i - w1 + 1, 256)
    }
    return substr(win2, i - w2 + 1, 1)
}

# Prints the value from position a up to b, masked unless it is shorter
# than 8 bytes and doesn't continue onto or from another line (forced).
function emit(a, b, forced,    r, k) {
    if (b <= a) return
    if (!forced && b - a < 8) {
        r = ""
        for (k = a; k < b; k++) r = r at(k)
        printf "%s", r
    } else printf "[REDACTED]"
}
