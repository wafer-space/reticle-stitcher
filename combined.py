#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
combine_oas_in_grid.py

This Python script generates a Magic EDA command file (Tcl) that combines all the
previously downloaded OAS files into a single large OAS file, placing them in a
grid specified by the first column in the same CSV manifest. It also renames
the top cell of each OAS file to ensure unique names (to prevent name clashes).

REQUIREMENTS:
1) Magic EDA must recognize the OAS file format via its CIF I/O.
2) The OAS files must already have been downloaded locally.
3) The CSV manifest must have at least two relevant fields:
   - The first column: a grid code such as 'A1', 'B2', etc.
   - The final column: the local OAS filename. (If your CSV has the same format as
     the downloader script, you might need to adapt the parsing logic below.

HOW IT WORKS:
1) We parse the CSV. For each row, we read the first column (e.g., 'A1'), which
   encodes a row/column in the final layout. We'll parse the letter(s) for the
   row index, the digit(s) for the column index.
2) We find the OAS filename (e.g., 'some_file.oas').
3) We produce commands in a Magic script that:
   - loads the OAS file (using CIF read if Magic recognizes OAS as a CIF variant),
   - obtains the top cell name for that newly read design,
   - renames that top cell to a unique name (including the grid code),
   - moves (translates) that cell to a location based on row/column.
4) After processing all OAS files, we save the entire design as a single OAS.

NOTE: The script below just creates a Tcl file ("combine_oas_script.tcl") that
you can run inside Magic with:

    magic -dnull -noconsole combine_oas_script.tcl

Then you'll have the single combined file ("combined.oas").

USAGE EXAMPLE:
    python combine_oas_in_grid.py path/to/manifest.csv --xspacing 2000 --yspacing 2000
    magic -dnull -noconsole combine_oas_script.tcl

By default, the script sets up a 1000u (user units) translation step in x and y.
You may adjust the spacing using command-line arguments.

TESTS:
We provide docstring tests for the coordinate parser function.

"""
import sys
import csv
import re
import argparse


def parse_grid_code(grid_code: str) -> (int, int):
    """
    Parse a code like "A1" or "B3" into (row, col) integers.
    We interpret the leading letters as the row (A=0, B=1, C=2, ...),
    and the trailing digits as the column (1-based -> 0-based, etc.).

    >>> parse_grid_code("A1")
    (0, 0)
    >>> parse_grid_code("B1")
    (1, 0)
    >>> parse_grid_code("B3")
    (1, 2)
    >>> parse_grid_code("AA10")
    (26, 9)
    """
    # Separate out letters vs digits
    match = re.match(r"^([A-Za-z]+)(\d+)$", grid_code)
    if not match:
        raise ValueError(f"Invalid grid code '{grid_code}'")
    letters = match.group(1).upper()
    digits = match.group(2)

    # Convert letters to row index
    # We treat letters like base-26, with A=0, B=1, ..., Z=25, AA=26, etc.
    row_idx = 0
    for c in letters:
        row_idx = row_idx * 26 + (ord(c) - ord('A') + 1)
    row_idx -= 1  # because A=1 in base-26 logic above, but we want A=0

    # Convert digits to col index, but treat them as 1-based => 0-based
    col_idx = int(digits) - 1
    return (row_idx, col_idx)


def extract_oas_filename(line: str) -> str:
    """
    Given one line from the CSV, which might look like:
        A1, 001, some-other, curl -k 'someurl' | base64 -d > out.oas, etc.
    we want to extract the final .oas filename. We can re-use the logic from the
    downloader parse_line_for_download_info, or simply do a quick parse.

    For simplicity, we look for a pattern > <filename>.oas or just .oas in the row.
    If your CSV differs, you might need to adapt this function.

    Returns the OAS filename, or raises ValueError if not found.

    This is a simplistic approach. If you're using the same format as the previous
    script, you can replicate the parse_line_for_download_info.
    """
    # We'll attempt to find something like  'base64 -d > some_output.oas'
    pattern = r">\s*(\S+\.oas)"
    m = re.search(pattern, line)
    if not m:
        raise ValueError(f"Could not find .oas filename in line: {line}")
    return m.group(1)


def main():
    parser = argparse.ArgumentParser(description="Generate Magic script to combine OAS files in a grid.")
    parser.add_argument("manifest", help="Path to the CSV manifest file")
    parser.add_argument("--output_script", default="combine_oas_script.tcl", help="Name of the Magic Tcl script to generate")
    parser.add_argument("--final_oas", default="combined.oas", help="Name of the final combined OAS file")
    parser.add_argument("--xspacing", type=int, default=2000, help="Distance (in Magic units) to shift each column")
    parser.add_argument("--yspacing", type=int, default=2000, help="Distance (in Magic units) to shift each row")
    args = parser.parse_args()

    rows = []
    with open(args.manifest, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for line in reader:
            # We expect the first column is something like 'A1' or 'B2', etc.
            if not line:
                continue
            grid_code = line[0].strip()

            # The entire row might have the final column or so with the 'curl...' command.
            # If the CSV is consistent with the previous script, the 4th column might contain it.
            # We'll just join the entire row to a single string for searching.
            joined = ",".join(line)

            try:
                oas_file = extract_oas_filename(joined)
            except ValueError:
                # If we can't parse, skip
                continue

            rows.append((grid_code, oas_file))

    if not rows:
        print("No OAS entries found in manifest. Exiting.")
        sys.exit(0)

    # Prepare to write the Magic script
    with open(args.output_script, "w") as out:
        out.write("# Auto-generated Magic script to combine OAS files in a grid\n")
        out.write("crashbackups stop\n")
        out.write("# Load your technology if needed, e.g.:\n")
        out.write("# tech load SCN6M_SUBM\n")
        out.write("box size 0 0\n")

        for (grid_code, oas_file) in rows:
            (row_idx, col_idx) = parse_grid_code(grid_code)
            x_off = col_idx * args.xspacing
            y_off = row_idx * args.yspacing

            # Step 1: read the OAS file
            out.write(f"cif read {oas_file}\n")

            # Step 2: find the top cell name
            out.write("set topcells [cif list top]\n")
            out.write("set topcell [lindex $topcells end]\n")  # we assume the newly read file's top cell is last
            # Alternatively, we might do [lindex $topcells 0], but let's pick last.

            # Step 3: rename it to something unique with the grid code
            # e.g. rename $topcell OAS_${grid_code}
            new_name = f"OAS_{grid_code}"
            out.write(f"rename $topcell {new_name}\n")

            # Step 4: move the cell to the desired offset
            out.write(f"select cell {new_name}\n")
            out.write(f"move by {x_off} {y_off}\n")

        # Finally, write out a single OAS file
        out.write(f"save {args.final_oas}\n")
        out.write("quit -noprompt\n")

    print(f"Wrote Magic combine script to {args.output_script}.")
    print("Run Magic via:  magic -dnull -noconsole {args.output_script}")


if __name__ == "__main__":
    main()
