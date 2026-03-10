# Note Format

This file captures the generalized note structure from the existing examples without repeating customer-specific private data.

## Core Pattern

Start with customer identity lines:

- Primary insured name and date of birth
- Secondary insured or household member names and dates of birth when present
- Driver's license or ID values when present
- Mailing address
- Email
- Phone
- Existing policy numbers with renewal or effective shorthand dates

Then add an auto section when present:

- Divider line
- Vehicle lines in the format `YY Make/Model or short label - VIN`
- Liability and other shorthand coverage lines
- Optional note fragments such as rideshare, towing, rental, or similar endorsements
- Divider line
- Premium header line like `- PREM -`
- Current premium or benchmark premium
- Carrier comparison lines such as `AIC6`, `AIC12`, `TRAV`, `AAA12`, `PROG`

Then add a home section when present:

- Strong divider line
- Home facts such as year built, square footage, deductible
- Coverage lines labeled with shorthand such as `A`, `B`, `C`, `D`, `E`
- Roof, contents, fences, carpets, ordinance/law, matching, service line, sewer/drain, or similar shorthand fields when shown
- Divider line
- Premium header line
- Home carrier comparison lines

## Style Rules

- Use plain text, not markdown tables.
- Keep lines compact.
- Preserve abbreviations exactly if the document already uses them.
- Prefer uppercase shorthand labels where the existing notes use them.
- Use separators such as:
  - `----------------------------------------------------`
  - `============================================`

## Caution

Do not expand abbreviations unless the user explicitly defines them.
If a value is uncertain, keep the raw value and flag it instead of guessing.
