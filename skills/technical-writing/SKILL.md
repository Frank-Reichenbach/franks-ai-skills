---
name: technical-writing
description: Improves clarity, structure, and tone of technical writing (docs, proposals, PR descriptions, client-facing write-ups) for a junior-friendly, easy-to-understand audience, choosing German or English as appropriate. Applies this plugin's default voice guidelines unless the project or an explicit request specifies otherwise. Not for authoring a skill's own SKILL.md content — see skill-writing for that. Use whenever writing or editing technical prose.
---

# Technical Writing

## Scope

Applies to prose written for someone to read later: documentation,
proposals, PR/commit descriptions, client-facing write-ups, READMEs,
explanatory comments longer than a line. Not code itself, and not a short
in-conversation reply that isn't meant to be reused or shared.

Not for authoring a skill's own `SKILL.md` — naming, the
description-as-classifier discipline, and progressive disclosure are
`skill-writing`'s job. `technical-writing` governs prose clarity and voice
elsewhere, including a skill's `references/*.md` content.

## Clarity rules (universal — apply regardless of audience or organization)

- **Short sentences.** One idea per sentence. If a sentence needs a comma
  to hold two claims, consider two sentences instead.
- **Lead with the point.** State the conclusion or the ask first, then the
  supporting detail — never bury the answer at the end of a paragraph.
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

## Language choice (German or English)

- Match the language of the request or the surrounding project by default.
- If genuinely ambiguous (no signal either way), default to English.
- Don't switch languages mid-document. If both languages are genuinely
  needed (for example, a glossary of German industry terms inside an
  English document), mark the switch explicitly rather than letting it
  drift.

## Tone and voice

This plugin ships a default voice in `references/default-voice.md` —
apply it unless the project's own conventions or an explicit request say
otherwise. It is a default, not a universal rule: an existing project's
established style, or the person asking, always wins.
