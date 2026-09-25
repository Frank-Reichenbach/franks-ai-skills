---
name: technical-writing
description: Improves clarity, structure, and tone of technical writing (docs, proposals, PR descriptions, commit messages, client-facing write-ups) for a junior-friendly, easy-to-understand audience, choosing German or English as appropriate. Informs rather than sells — no self-praise or reassurance. Applies this plugin's default voice to client-facing text and a plain, factual voice to engineering text, unless the project or an explicit request specifies otherwise. Not for authoring a skill's own SKILL.md content — see skill-writing for that. Use whenever writing or editing technical prose.
---

# Technical Writing

## Scope

Applies to prose written for someone to read later: documentation,
proposals, PR/commit descriptions, review comments, issues, client-facing
write-ups, READMEs, explanatory comments longer than a line. Not code
itself, and not a short in-conversation reply that isn't meant to be
reused or shared.

Not for authoring a skill's own `SKILL.md` — naming, the
description-as-classifier discipline, and progressive disclosure are
`skill-writing`'s job. `technical-writing` governs prose clarity and voice
elsewhere, including a skill's `references/*.md` content. Not for *what*
a commit message or PR description has to contain, or how it's wrapped —
see `git-flow` for that; this skill decides how it's worded.

When reviewing an existing document, quote or reproduce only the parts
that need to change — not the whole document.

## Procedure

1. **Identify the reader and the artifact.** Client-facing text
   (proposals, customer documentation, write-ups for a client) or
   engineering text (commit messages, PR descriptions, review comments,
   issues, READMEs, code documentation). This decides the voice — see
   "Tone and voice".
2. **Pick the language** — see "Language choice".
3. **Write or revise** with the clarity rules below.
4. **Run the no-editorializing tests** on every sentence and cut what
   fails.
5. **When reviewing**, return only the passages that change, each with a
   one-line reason.

## Clarity rules (universal — apply regardless of audience or organization)

- **Short sentences.** One idea per sentence. If a sentence needs a comma
  to hold two claims, consider two sentences instead.
- **Lead with the point.** State the conclusion or the ask first, then the
  supporting detail — never bury the answer at the end of a paragraph.
  For a change description, that is the state after the change ("When
  this merges, X does Y").
- **Write for a junior reader.** Don't assume unexplained jargon, acronyms,
  or tool-specific shorthand. If a term is genuinely necessary, define it
  on first use.
- **Unambiguous structure.** Headings that describe what's under them,
  short paragraphs, bullet lists where the content is genuinely a list —
  not prose forced into bullet shape, and not a list that should be prose.
- **Active voice, concrete verbs.** "The script deletes the file" over
  "the file gets deleted" or "the file is deleted by the script."
- **Cut what the reader already knows.** Don't explain what well-named
  code or an obvious step already shows; explain the non-obvious part —
  the why, the constraint, the tradeoff.
- **Wrapping in `.md` files:** match the file's existing line wrapping.

## No editorializing — inform, don't sell

Write about what the change or the thing *does*, not about how good,
clean, or careful the work is. The reader has the artifact; anything that
only flatters it or reassures them adds nothing, and to a reviewer it
reads as salesmanship. This is a matter of tone, not a word list. Three
tests before a sentence stays:

1. **Deletion** — remove the phrase. If the reader lost no fact, cut it.
2. **Subject** — is the sentence about the change, or about the author
   and their diligence? The latter goes.
3. **Voice** — would a terse maintainer write this, or does it read like
   a cover letter?

Two recurring failure modes:

- **Announcing the expected.** Passing tests, clean linters, "no
  regressions", "works as expected" are the baseline. State a check's
  status only to flag an exception (something knowingly failing or
  skipped). In a test or verification list, say what was added or
  covered, not that it is green.
- **Self-praise and reassurance.** "Robust", "clean", "thoroughly
  tested", "verified, not assumed", "deliberately scoped", "I made sure
  to…". Show the fact; drop the framing.

Use plain labels: "Tests", "Limitations", "Breaking change" — not
"Tests (all green)".

## Language choice (German or English)

- Match the language of the request or the surrounding project by default.
- If genuinely ambiguous (no signal either way), default to English.
- Don't switch languages mid-document. If both languages are genuinely
  needed (for example, a glossary of German industry terms inside an
  English document), mark the switch explicitly rather than letting it
  drift.

## Tone and voice

- **Client-facing text:** apply this plugin's default voice in
  `references/default-voice.md`.
- **Engineering text:** plain and factual. The default voice's
  character (humour, mission, third-person brand name) doesn't apply;
  its "Don't" list does.
- Both are defaults: an existing project's established style, or the
  person asking, always wins.

## Stop and ask

- The reader is unclear and it changes the voice — for example, a text
  that might go to a client or might stay internal.
- The request conflicts with the project's established style and it's
  ambiguous which should win.

## Output

The finished text in the chosen language and voice — or, for a review,
the changed passages with a one-line reason each. No commentary on how
the text was improved.
