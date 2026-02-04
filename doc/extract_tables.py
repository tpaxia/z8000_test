#!/usr/bin/env python3
"""
Extract addressing mode, syntax, and encoding tables from Z8000 instruction PDF.
"""

import re
import pdfplumber
import csv
import sys
from dataclasses import dataclass


@dataclass
class InstructionEntry:
    addressing_mode: str
    syntax: str
    encoding: str


def extract_tables_from_pdf(pdf_path: str) -> list[InstructionEntry]:
    """Extract addressing mode tables from the PDF."""
    entries = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            # Extract tables from the page
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                # Check if this looks like an addressing mode table
                # by looking for header row with "Addressing", "Assembly Syntax", "Encoding"
                header_row_idx = None
                for i, row in enumerate(table):
                    if row and any(cell and 'Addressing' in str(cell) for cell in row):
                        header_row_idx = i
                        break

                if header_row_idx is None:
                    continue

                # Process rows after the header
                current_mode = None
                for row in table[header_row_idx + 1:]:
                    if not row or all(cell is None or cell == '' for cell in row):
                        continue

                    # Clean up the row data
                    cleaned = [str(cell).strip() if cell else '' for cell in row]

                    # Skip if it looks like a header or clock-only row
                    if len(cleaned) < 2:
                        continue

                    # Extract addressing mode (first column, may span multiple rows)
                    mode = cleaned[0].replace(':', '').strip() if cleaned[0] else current_mode
                    if mode and mode not in ['', 'Modes']:
                        current_mode = mode

                    # Extract syntax (second column)
                    syntax = cleaned[1] if len(cleaned) > 1 else ''

                    # Extract encoding (third column)
                    encoding = cleaned[2] if len(cleaned) > 2 else ''

                    # Skip header rows or empty syntax
                    if not syntax or syntax == 'Assembly Syntax' or 'Addressing' in syntax:
                        continue

                    # Clean up encoding - remove clock info if mixed in
                    encoding = re.sub(r'\s+\d+$', '', encoding)

                    if current_mode and syntax:
                        entries.append(InstructionEntry(
                            addressing_mode=current_mode,
                            syntax=syntax,
                            encoding=encoding
                        ))

    return entries


def extract_tables_regex(pdf_path: str) -> list[InstructionEntry]:
    """Alternative extraction using regex patterns on text."""
    entries = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            current_mode = None
            pending_entry = None  # For multi-word encodings

            for i, line in enumerate(lines):
                # Look for addressing mode patterns
                # Format: "R: CLR Rd 10001101_Rddd_1000 7"
                # or "IR: CALL @Rd 00011111_Rdnz_0000 10"
                # or "IM: ADD Rd, #data 00000001_0000_Rddd 7"
                # or "X: CLRaddr(Rd) 01001101_Rdnz_1000 12" (no space)
                match = re.match(
                    r'^\s*(R|IR|DA|X|RA|IM|BA|BX):\s*'    # Addressing mode with colon
                    r'(.+?)\s+'                           # Syntax (greedy match until encoding)
                    r'([01][\w_]+)\s*'                    # Encoding (starts with 0 or 1)
                    r'(?:\d+(?:\s*\+\s*\d+\w)?)?$',       # Optional clocks (e.g., "7" or "11 + 9n")
                    line
                )

                if match:
                    # Save any pending entry first
                    if pending_entry:
                        entries.append(pending_entry)

                    mode = match.group(1)
                    syntax = match.group(2).strip()
                    encoding = match.group(3).strip()
                    current_mode = mode

                    # Clean up syntax - fix run-together text
                    syntax = re.sub(r'([A-Z]+B?)(addr|@)', r'\1 \2', syntax)  # "CLRaddr" -> "CLR addr"
                    syntax = re.sub(r'^([A-Z]+B?)(RR[a-z])', r'\1 \2', syntax)  # "ADDLRRd" -> "ADDL RRd"
                    syntax = re.sub(r'^([A-Z]+B?)(RQ[a-z])', r'\1 \2', syntax)  # "EXTSLRQd" -> "EXTSL RQd"
                    syntax = re.sub(r'^([A-Z]+B?)(R[a-z])', r'\1 \2', syntax)  # "ADCRd" -> "ADC Rd"
                    syntax = re.sub(r',(\S)', r', \1', syntax)  # "Rd,Rs" -> "Rd, Rs"

                    pending_entry = InstructionEntry(
                        addressing_mode=mode,
                        syntax=syntax,
                        encoding=encoding
                    )
                    continue

                # Check for continuation lines (multi-word encodings)
                # Don't commit entry yet - there may be more continuation lines
                stripped = line.strip()

                # Skip page numbers (just digits, typically 2-3 digits)
                if re.match(r'^\d{1,3}$', stripped):
                    continue

                # Format: "0000_Rddd_0000_0000" (binary encoding word with underscores)
                encoding_only = re.match(r'^([01][\w_]*_[\w_]+)\s*$', stripped)
                if encoding_only and pending_entry:
                    pending_entry.encoding += ' + ' + encoding_only.group(1).strip()
                    continue

                # Format: "address" or "displacement"
                if stripped in ('address', 'displacement') and pending_entry:
                    pending_entry.encoding += ' + ' + stripped
                    continue

                # Format: "#data", "#data (high)", "#data (low)", "#data | #data"
                data_match = re.match(r'^(#data(?:\s*\([^)]+\))?(?:\s*\|\s*#data)?)\s*$', stripped)
                if data_match and pending_entry:
                    pending_entry.encoding += ' + ' + data_match.group(1).strip()
                    continue

                # Check for lines without mode prefix but with instruction
                # (byte variant under same addressing mode, e.g., "BITB Rbd, Rs")
                # or standalone instructions like NOP, HALT
                # Format: "CLRB Rbd 10001100_Rbdd_1000 7" or "NOP 10001101_0000_0111 7"
                match2 = re.match(
                    r'^([A-Z][\w@#,\s()]+?)\s+([01][\w_]+)\s*(?:\d+(?:\s*\+\s*\d+\w)?)?$',
                    line
                )
                if match2:
                    syntax = match2.group(1).strip()
                    encoding = match2.group(2).strip()

                    # Skip if this looks like a header, note, page number, or garbage
                    if (syntax.startswith('Note') or 'Addressing' in syntax or
                        'Assembly' in syntax or 'Modes' in syntax or
                        'Chapter' in syntax or 'Operation' in syntax or
                        syntax.isdigit() or len(syntax) < 2 or
                        # Skip timing table entries (multiple numbers in syntax)
                        len(re.findall(r'\d+', syntax)) > 2):
                        if pending_entry:
                            entries.append(pending_entry)
                            pending_entry = None
                        continue

                    # Clean up syntax - fix run-together text
                    syntax = re.sub(r'^([A-Z]+B?)(RR[a-z])', r'\1 \2', syntax)  # "ADDLRRd" -> "ADDL RRd"
                    syntax = re.sub(r'^([A-Z]+B?)(RQ[a-z])', r'\1 \2', syntax)  # "EXTSLRQd" -> "EXTSL RQd"
                    syntax = re.sub(r'^([A-Z]+B)(R[a-z])', r'\1 \2', syntax)  # "CLRBRbd" -> "CLRB Rbd"
                    syntax = re.sub(r'^([A-Z]+)(R[a-z])', r'\1 \2', syntax)  # "ADDRd" -> "ADD Rd"
                    syntax = re.sub(r'([A-Z]+B?)(addr|@)', r'\1 \2', syntax)  # "CLRaddr" -> "CLR addr"
                    syntax = re.sub(r',(\S)', r', \1', syntax)  # "Rd,Rs" -> "Rd, Rs"

                    # Save pending entry first
                    if pending_entry:
                        entries.append(pending_entry)

                    # Use "-" for instructions without addressing mode (like NOP, HALT)
                    pending_entry = InstructionEntry(
                        addressing_mode=current_mode if current_mode else "-",
                        syntax=syntax,
                        encoding=encoding
                    )
                    continue

                # If we hit an unrelated line, save pending entry
                if pending_entry and not line.strip().startswith(('0', '1', 'address', '#data')):
                    # Check if this line could be a different mode
                    if re.match(r'^\s*(R|IR|DA|X|RA|IM|BA|BX):', line):
                        pass  # Will be handled in next iteration
                    elif line.strip() and not re.match(r'^\d+$', line.strip()):
                        entries.append(pending_entry)
                        pending_entry = None

            # Don't forget last pending entry
            if pending_entry:
                entries.append(pending_entry)

    return entries


def merge_multiword_encodings(entries: list[InstructionEntry]) -> list[InstructionEntry]:
    """Merge entries where encoding spans multiple words."""
    merged = []
    i = 0

    while i < len(entries):
        entry = entries[i]

        # Check if next entry might be a continuation (same mode, encoding looks like second word)
        if (i + 1 < len(entries) and
            entries[i + 1].addressing_mode == entry.addressing_mode and
            'address' in entries[i + 1].syntax.lower()):
            # This might be a multi-word encoding
            pass

        merged.append(entry)
        i += 1

    return merged


def output_table(entries: list[InstructionEntry], format: str = 'markdown'):
    """Output the extracted entries as a table."""

    if format == 'markdown':
        print("| Addressing Mode | Assembly Syntax | Encoding |")
        print("|-----------------|-----------------|----------|")
        for entry in entries:
            print(f"| {entry.addressing_mode} | {entry.syntax} | `{entry.encoding}` |")

    elif format == 'csv':
        writer = csv.writer(sys.stdout)
        writer.writerow(['Addressing Mode', 'Assembly Syntax', 'Encoding'])
        for entry in entries:
            writer.writerow([entry.addressing_mode, entry.syntax, entry.encoding])

    elif format == 'plain':
        print(f"{'Mode':<6} {'Syntax':<25} {'Encoding'}")
        print("-" * 70)
        for entry in entries:
            print(f"{entry.addressing_mode:<6} {entry.syntax:<25} {entry.encoding}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract addressing mode tables from Z8000 instruction PDFs'
    )
    parser.add_argument('pdf_file', help='Path to the PDF file')
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'csv', 'plain'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )

    args = parser.parse_args()

    # Try table extraction first, fall back to regex
    entries = extract_tables_from_pdf(args.pdf_file)

    if not entries:
        print("Table extraction found no results, trying regex method...", file=sys.stderr)
        entries = extract_tables_regex(args.pdf_file)

    if not entries:
        print("No addressing mode tables found in the PDF.", file=sys.stderr)
        sys.exit(1)

    # Remove duplicates while preserving order
    seen = set()
    unique_entries = []
    for entry in entries:
        key = (entry.addressing_mode, entry.syntax, entry.encoding)
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    if args.output:
        with open(args.output, 'w') as f:
            old_stdout = sys.stdout
            sys.stdout = f
            output_table(unique_entries, args.format)
            sys.stdout = old_stdout
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        output_table(unique_entries, args.format)


if __name__ == '__main__':
    main()
