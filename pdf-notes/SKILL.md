---
name: pdf-notes
description: Use when the user asks to "make notes for" a customer, create notes from insurance PDFs, read PDFs in Downloads, extract structured data from customer Home or Auto PDF files, or format notes to match the existing GM+Notes and LF+Notes style. Triggers include phrases like "make notes for", "notes for", "read the PDFs for", and "summarize the customer PDFs".
---

# PDF Notes

## Overview

This skill creates customer notes from PDFs stored in `%USERPROFILE%\Downloads`.
Use it when the user wants notes for a customer and the source PDFs follow the naming pattern `{FirstName}{LastName}Home.pdf` or `{FirstName}{LastName}Auto.pdf`.
The current implementation is customized for Home PDFs and fills `%USERPROFILE%\Downloads\NotesTemplate.txt`.

## Workflow

1. Interpret the user request `make notes for {customer}` as a request to find that customer's PDFs in `Downloads`, extract relevant policy and customer details, and write a notes text file using `NotesTemplate.txt`.
2. Search `%USERPROFILE%\Downloads` for matching PDFs.
   - Expected files are named with no separator between first and last name, plus `Home` or `Auto`.
   - Examples: `LauraFolloHome.pdf`, `LauraFolloAuto.pdf`, `GetachewMollaAuto.pdf`
   - Prefer exact normalized matches first, then looser matches if needed.
3. For Home PDFs, use `NotesTemplate.txt` in `Downloads` as the output shape.
   - Any field wrapped in `{}` should be treated as a label-driven extraction target.
   - Search for the same label text in the PDF, allowing only whitespace differences caused by PDF extraction.
   - Write the output line as `Label: value`.
4. Use [scripts/generate_home_notes.py](scripts/generate_home_notes.py) for the current Home workflow.
   - By default it writes generated notes into `pdf-notes/generated/`.
   - If the user specifically wants the finished `.txt` copied into `Downloads`, do that as a separate shell step after generation.
5. If a field is not present in the PDF, keep the line and leave the value blank instead of guessing.

## Output Rules

- Write a new `.txt` file.
- Default script output goes to `pdf-notes/generated/`.
- If requested, copy the final `.txt` to `Downloads` after generation.
- Follow `NotesTemplate.txt` line order.
- Replace `{label}` placeholders with `label: extracted value`.
- Preserve the example note style only where it does not conflict with the template.
- The current customized template is Home-only. Do not assume Auto extraction rules yet.

## Resources

### Script

Use [scripts/find_matching_pdfs.py](scripts/find_matching_pdfs.py) to locate candidate files in `Downloads` for a customer name before reading PDFs manually.
Use [scripts/generate_home_notes.py](scripts/generate_home_notes.py) to generate a Home notes file from `NotesTemplate.txt`.

### Reference

Use [references/note-format.md](references/note-format.md) for the generalized structure derived from `GM+Notes.txt` and `LF+Notes.txt`.

## Known Local References

These existing note examples define the target style when they exist in the current user's profile:

- `%USERPROFILE%\OneDrive\Documents\ALL Dec Pages\GM+Notes.txt`
- `%USERPROFILE%\OneDrive\Documents\ALL Dec Pages\LF+Notes.txt`

If the user later updates those examples, re-check them before changing the skill.

## Pending Customization

The Home template customization has been provided.
Auto extraction rules are still pending and should be added to this skill when the user provides them.
