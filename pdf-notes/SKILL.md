---
name: pdf-notes
description: Use when the user asks to "make notes for" a customer, create notes from insurance PDFs, read PDFs in Downloads, extract structured data from customer Home or Auto PDF files, or format notes to match the existing GM+Notes and LF+Notes style. Triggers include phrases like "make notes for", "notes for", "read the PDFs for", and "summarize the customer PDFs".
---

# PDF Notes

## Overview

This skill creates customer notes from PDFs stored in `C:\Users\moham\Downloads`.
Use it when the user wants notes for a customer and the source PDFs follow the naming pattern `{FirstName}{LastName}Home.pdf` or `{FirstName}{LastName}Auto.pdf`.

## Workflow

1. Interpret the user request `make notes for {customer}` as a request to find that customer's PDFs in `Downloads`, extract relevant policy and customer details, and draft notes in the established notes format.
2. Search `C:\Users\moham\Downloads` for matching PDFs.
   - Expected files are named with no separator between first and last name, plus `Home` or `Auto`.
   - Examples: `LauraFolloHome.pdf`, `LauraFolloAuto.pdf`, `GetachewMollaAuto.pdf`
   - Prefer exact normalized matches first, then looser matches if needed.
3. Read the PDFs and extract the required information.
   - Start with text extraction.
   - If extraction is poor because the PDF is scanned or image-based, say so clearly and use the best recoverable text.
4. Format the notes to match the patterns documented in [references/note-format.md](references/note-format.md).
5. Until the user provides the final extraction rules, do not invent missing business meaning.
   - If a field is visible but its meaning is unclear, preserve the value and label it conservatively.
   - If the user has not yet defined where a field belongs, place it in a short `Needs Mapping` section at the end.

## Output Rules

- Match the terse, line-oriented style of the existing note examples.
- Keep section separators simple using repeated dashes or equals signs.
- Preserve carrier abbreviations, premium shorthand, and coverage shorthand exactly when visible in the PDFs.
- Prefer one plain-text note block unless the user asks for another format.
- When both Auto and Home files exist, combine them into one note in the same style as the examples.

## Resources

### Script

Use [scripts/find_matching_pdfs.py](scripts/find_matching_pdfs.py) to locate candidate files in `Downloads` for a customer name before reading PDFs manually.

### Reference

Use [references/note-format.md](references/note-format.md) for the generalized structure derived from `GM+Notes.txt` and `LF+Notes.txt`.

## Known Local References

These existing note examples define the target style:

- `C:\Users\moham\OneDrive\Documents\ALL Dec Pages\GM+Notes.txt`
- `C:\Users\moham\OneDrive\Documents\ALL Dec Pages\LF+Notes.txt`

If the user later updates those examples, re-check them before changing the skill.

## Pending Customization

The user intends to provide:

- The exact data points that must be extracted from Home PDFs
- The exact data points that must be extracted from Auto PDFs
- The meaning of abbreviations and where each field belongs in the final note

When that information is provided, update this skill instead of keeping the logic only in chat.
