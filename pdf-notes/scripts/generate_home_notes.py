#!/usr/bin/env python3
"""
Generate home-policy notes from a matching PDF and NotesTemplate.txt.

Usage:
    python generate_home_notes.py "Katherine Holland"
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader

from find_matching_pdfs import find_candidates, normalize


DOWNLOADS = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"
DEFAULT_TEMPLATE = DOWNLOADS / "NotesTemplate.txt"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated"
DEFAULT_OUTPUT_SUFFIX = "Notes.txt"

VALUE_PATTERN = r"(Replacement Cost|Actual Cash Value|Extended Replacement Cost|Scheduled|Covered|Not Covered)"
PLAIN_LABELS = (
    "Date of birth",
    "Social security number",
    "Drivers license #",
    "Phone number",
    "Discounts",
)


def read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def clean_value(value: str) -> str:
    value = value.replace("\r", " ")
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r",(?=\D)", ", ", value)
    value = re.sub(r"(?<=\d),\s+(?=\d)", ",", value)
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    return value.strip(" :")


def clean_label(value: str) -> str:
    value = value.replace("\r", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def search(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return clean_value(match.group(1))


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def extract_names(text: str, customer: str) -> tuple[tuple[str, str], tuple[str, str]]:
    raw = search(text, r"Named Insured\(s\):\s*(.*?)e-mail\s*Address\(es\):")
    raw = re.sub(r"\d.*$", "", raw).strip()
    parts = [clean_value(part) for part in re.split(r"\band\b", raw, flags=re.IGNORECASE) if clean_value(part)]
    if len(parts) < 2:
        name = split_name(parts[0]) if parts else ("", "")
        return name, ("", "")

    customer_norm = normalize(customer)
    if normalize(parts[1]) == customer_norm and normalize(parts[0]) != customer_norm:
        parts = [parts[1], parts[0]]

    return split_name(parts[0]), split_name(parts[1])


def extract_discounts(text: str) -> tuple[str, str, str]:
    block = search(text, r"Discounts Applied to Policy.*?Discount Type Discount Type(.*?)Total Discount Savings")
    names = (
        "Preferred Payment Plan",
        "Claim Free",
        "Auto/Home Good Payer",
        "Non Smoker",
        "ePolicy",
        "New Roof",
    )
    found = [name for name in names if re.search(re.escape(name), block, re.IGNORECASE)]
    return ", ".join(found), ("Yes" if "Non Smoker" in found else ""), ("Yes" if "New Roof" in found else "")


def extract_loss_settlement_values(text: str) -> dict[str, str]:
    match = re.search(
        rf"Roof Materials\s*Wall-to-Wall Carpet\s*Fence\s*Rest of Dwelling\s*"
        rf"{VALUE_PATTERN}\s*{VALUE_PATTERN}\s*{VALUE_PATTERN}\s*{VALUE_PATTERN}\s*"
        rf"Personal Property Contents.*?{VALUE_PATTERN}",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return {}

    values = [clean_value(group) for group in match.groups()]
    return {
        "Roof Materials": values[0],
        "Wall-to-Wall Carpet": values[1],
        "Fence": values[2],
        "Rest of Dwelling": values[3],
        "Personal Property Contents (Pays up to the limit for Coverage C)": values[4],
    }


def extract_fields(text: str, customer: str) -> dict[str, str]:
    (first_name, first_last), (second_first, second_last) = extract_names(text, customer)
    discounts, non_smoker, new_roof = extract_discounts(text)
    loss_settlement = extract_loss_settlement_values(text)
    coverage_a_match = re.search(
        r"Coverage A - Dwelling\s*Extended Replacement Cost\(In Addition to Coverage A Limit\)"
        r"(\$[0-9]{1,3}(?:,[0-9]{3})*)(\d+%)\s*\(\$[0-9,]+\)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    fields = {
        "First name": first_name,
        "Last Name": first_last,
        "Second named insured First name": second_first,
        "Second named insured Last Name": second_last,
        "Date of birth": "",
        "Date of birth__2": "",
        "Social security number": "",
        "Social security number__2": "",
        "Drivers license #": "",
        "Drivers license #__2": "",
        "Phone number": "",
        "e-mail Address(es):": search(text, r"e-mail\s*Address\(es\):\s*(.*?)Property Insured:"),
        "Property Insured": search(text, r"Property Insured:\s*(.*?)Underwritten By:"),
        "Policy Number:": search(text, r"Policy Number:\s*([A-Z0-9-]+?)(?=Effective:)"),
        "Effective:": search(text, r"Effective:\s*([0-9/]+?)(?=\d{1,2}:\d{2}\s*[AP]M)"),
        "Year Built": search(text, r"Year Built:\s*([0-9]{4})"),
        "Square Footage": search(text, r"Square Footage:\s*([0-9,]+)"),
        "Style or Number of Stories": search(text, r"Style or Number of Stories:\s*(.*?)Dwelling Quality Grade:").removesuffix(" Material"),
        "Dwelling Quality Grade": search(text, r"Dwelling Quality Grade:\s*(.*?)Basement:"),
        "Foundation Type": search(text, r"Foundation Type:\s*(.*?)Number of Units:"),
        "Foundation Shape:": search(text, r"Foundation Shape:\s*(.*?)Please note"),
        "Roof Material:": search(text, r"Roof Material:\s*(.*?)Year Built:"),
        "Garage Type:": search(text, r"Garage Type:\s*(.*?)Square Footage:"),
        "Interior Wall Construction": search(text, r"Interior Wall Construction\s*(.*?)Style or Number of Stories:"),
        "Basement:": search(text, r"Basement:\s*(.*?)Foundation Type:"),
        "Number of Units:": search(text, r"Number of Units:?\s*([0-9]+)"),
        "Age of Roof": search(text, r"Age of Roof\s*([0-9]+)"),
        "Roof Type": search(text, r"Roof Type\s*(.*?)Number of Units"),
        "Roof Surface Material Type": search(text, r"Roof Surface Material Type\s*(.*?)Property Coverage"),
        "Construction Type": search(text, r"Construction Type\s*(.*?)Occupancy"),
        "Deductible": search(
            text,
            r"DeductibleType of Loss DeductibleApplicable to each covered loss\s*(\$[0-9,]+)",
        ),
        "Current Coverage A (Dwelling) Amount with Reconstruction Cost Factor:": search(
            text,
            r"Current Coverage A \(Dwelling\) Amount with Reconstruction Cost Factor:\s*(\$[0-9,]+)",
        ),
        "Recalculated Reconstruction Cost Estimate:": search(
            text,
            r"Recalculated Reconstruction Cost Estimate:\s*(\$[0-9,]+)",
        ),
        "Coverage A (Dwelling) Amount offered for this renewal:": search(
            text,
            r"Coverage A \(Dwelling\) Amount offered for this renewal:\s*(\$[0-9,]+)",
        ),
        "Coverage A - Dwelling": clean_value(coverage_a_match.group(1)) if coverage_a_match else "",
        "Extended Replacement Cost %": clean_value(coverage_a_match.group(2)) if coverage_a_match else "",
        "Coverage B - Separate Structures": search(
            text,
            r"Coverage B - Separate Structures\s*(\$[0-9,]+)",
        ),
        "Coverage C - Personal Property": search(
            text,
            r"Coverage C - Personal Property\s*Contents Replacement Coverage\s*(\$[0-9,]+)",
        ),
        "Coverage D - Loss of Use": search(
            text,
            r"Coverage D - Loss of Use\s*Additional Living Expense Term\s*(\$[0-9,]+)",
        ),
        "Coverage F - Medical Payments to Others": search(
            text,
            r"Coverage F - Medical Payments to Others\s*(\$[0-9,]+)",
        ),
        "Coverage E - Personal Liability": search(
            text,
            r"Coverage E - Personal Liability\s*(\$[0-9,]+)",
        ),
        "Building Ordinance or Law": (
            search(
                text,
                r"Building Ordinance or Law\((.*?)\)\s*Coverage A\s*Coverage B\s*(\$[0-9,]+)\s*(\$[0-9,]+)",
            )
        ),
        "Sewer & Drain Damage": search(
            text,
            r"Sewer\s*&\s*Drain Damage - Extended Contents\s*(\$[0-9,]+)",
        ),
        "Limited Matching Coverage for Siding and Roof Materials": search(
            text,
            r"Limited Matching Coverage for Siding and\s*Roof Materials\s*(\$[0-9,]+)",
        ),
        "Roof Materials": loss_settlement.get("Roof Materials", ""),
        "Wall-to-Wall Carpet": loss_settlement.get("Wall-to-Wall Carpet", ""),
        "Fence": loss_settlement.get("Fence", ""),
        "Rest of Dwelling": loss_settlement.get("Rest of Dwelling", ""),
        "Personal Property Contents (Pays up to the limit for Coverage C)": loss_settlement.get(
            "Personal Property Contents (Pays up to the limit for Coverage C)",
            "",
        ),
        "1st Mortgagee": search(text, r"1st MortgageeLoan Number\s*(.*?)\s*\d{6,}\s*Policy and Endorsements"),
        "Loan Number": search(text, r"1st MortgageeLoan Number\s*.*?\s+(\d{6,})\s*Policy and Endorsements"),
        "Discounts": discounts,
        "Non Smoker": non_smoker,
        "New Roof": new_roof,
        "Policy Premium": search(text, r"Policy Premium\s*(\$[0-9,]+(?:\.\d{2})?)"),
    }

    ordinance = re.search(
        r"Building Ordinance or Law\((.*?)\)\s*Coverage A\s*Coverage B\s*(\$[0-9,]+)\s*(\$[0-9,]+)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if ordinance:
        fields["Building Ordinance or Law"] = (
            f"{clean_value(ordinance.group(1))}; "
            f"Coverage A {clean_value(ordinance.group(2))}; "
            f"Coverage B {clean_value(ordinance.group(3))}"
        )

    return fields


def render_template(template_text: str, fields: dict[str, str]) -> str:
    counters: dict[str, int] = {}

    def replace_token(match: re.Match[str]) -> str:
        raw_label = clean_label(match.group(1))

        if raw_label == "First name":
            value = fields.get(raw_label, "")
            return f"{value} " if value and fields.get("Last Name") else value
        if raw_label == "Last Name":
            return fields.get(raw_label, "")
        if raw_label == "Second named insured First name":
            value = fields.get(raw_label, "")
            return f"{value} " if value and fields.get("Second named insured Last Name") else value
        if raw_label == "Second named insured Last Name":
            return fields.get(raw_label, "")

        value = fields.get(raw_label, "")
        if raw_label.endswith(":"):
            return f"{raw_label} {value}".rstrip()
        return f"{raw_label}: {value}".rstrip()

    rendered = re.sub(r"\{([^{}]+)\}", replace_token, template_text, flags=re.DOTALL)

    lines: list[str] = []
    for line in rendered.splitlines():
        label = clean_label(re.sub(r"\s*\(if found\)", "", line))
        if label in PLAIN_LABELS:
            counters[label] = counters.get(label, 0) + 1
            key = label if counters[label] == 1 else f"{label}__{counters[label]}"
            value = fields.get(key, fields.get(label, ""))
            lines.append(f"{label}: {value}".rstrip())
            continue

        lines.append(re.sub(r"\s*\(if found\)", "", line).rstrip())

    return "\n".join(lines).rstrip() + "\n"


def choose_home_pdf(customer: str) -> Path:
    for candidate in find_candidates(customer):
        if candidate.stem.lower().endswith("home"):
            return candidate
    raise FileNotFoundError(f"No matching home PDF found for {customer!r}.")


def build_output_path(customer: str) -> Path:
    compact_name = re.sub(r"[^A-Za-z0-9]", "", customer)
    return DEFAULT_OUTPUT_DIR / f"{compact_name}{DEFAULT_OUTPUT_SUFFIX}"


def write_output(output_path: Path, rendered: str) -> None:
    try:
        output_path.write_text(rendered, encoding="utf-8")
        return
    except PermissionError:
        pass

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        suffix=".txt",
        dir=Path.cwd(),
    ) as handle:
        handle.write(rendered)
        temp_path = Path(handle.name)

    try:
        try:
            shutil.copyfile(temp_path, output_path)
            return
        except PermissionError:
            temp_literal = str(temp_path).replace("'", "''")
            output_literal = str(output_path).replace("'", "''")
            command = (
                "Copy-Item -LiteralPath "
                f"'{temp_literal}' "
                "-Destination "
                f"'{output_literal}' -Force"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=True,
            )
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("customer", help="Customer first and last name")
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        help="Path to NotesTemplate.txt",
    )
    parser.add_argument(
        "--output",
        help="Optional output path for the generated notes file",
    )
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    pdf_path = choose_home_pdf(args.customer)
    output_path = Path(args.output) if args.output else build_output_path(args.customer)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    template_text = template_path.read_text(encoding="utf-8")
    pdf_text = read_pdf_text(pdf_path)
    fields = extract_fields(pdf_text, args.customer)
    rendered = render_template(template_text, fields)
    write_output(output_path, rendered)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
