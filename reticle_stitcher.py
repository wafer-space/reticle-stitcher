# SPDX-FileCopyrightText: 2025 Wafer Space PTE. LTD. <info@wafer.space>
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import argparse

import pya

# Constants
RETICLE_WIDTH = 32000
RETICLE_HEIGHT = 26000

SEAL_RING_SIZE = 25

USER_PROJECT_WIDTH = 3880
USER_PROJECT_HEIGHT = 5070
user_project_name = "caravel_18019f00"

SAW_STREET_HORIZONTAL = 66.6
SAW_STREET_VERTICAL = 62.2
SAW_STREET_MINIMUM = 60

NUM_PROJECTS_HORIZONTAL = 8
NUM_PROJECTS_VERTICAL = 5
NUM_PROJECTS_TOTAL = NUM_PROJECTS_HORIZONTAL * NUM_PROJECTS_VERTICAL

SPACING_HORIZONTAL = (
    RETICLE_WIDTH
    - (SAW_STREET_VERTICAL + 2 * SEAL_RING_SIZE) * (NUM_PROJECTS_HORIZONTAL - 1)
    - USER_PROJECT_WIDTH * NUM_PROJECTS_HORIZONTAL
) / 2
SPACING_VERTICAL = (
    RETICLE_HEIGHT
    - (SAW_STREET_HORIZONTAL + 2 * SEAL_RING_SIZE) * (NUM_PROJECTS_VERTICAL - 1)
    - USER_PROJECT_HEIGHT * NUM_PROJECTS_VERTICAL
) / 2


def stitch_reticle(user_project_path, user_project_cellname):

    layout = pya.Layout()
    top_cell = layout.create_cell("reticle")

    # Create boundary (for debugging)
    PR_bndry = pya.LayerInfo(0, 0)
    top_cell.shapes(PR_bndry).insert(pya.DBox.new(0, 0, RETICLE_WIDTH, RETICLE_HEIGHT))

    # Read the user project
    layout.read(user_project_path)
    user_project_cell = layout.cell(user_project_cellname)

    # Insert 40 user projects
    top_cell.insert(
        pya.DCellInstArray(
            user_project_cell.cell_index(),
            pya.DPoint(SPACING_HORIZONTAL, SPACING_VERTICAL),
            pya.DVector(
                USER_PROJECT_WIDTH + SAW_STREET_VERTICAL + 2 * SEAL_RING_SIZE, 0
            ),
            pya.DVector(
                0, USER_PROJECT_HEIGHT + SAW_STREET_HORIZONTAL + 2 * SEAL_RING_SIZE
            ),
            8,
            5,
        )
    )

    # Get the seal ring library
    lib = pya.Library.library_by_name("gf180mcu_seal_ring")

    # Create the seal ring PCell
    pcell_decl = lib.layout().pcell_declaration("seal_ring")
    param = {
        "w": USER_PROJECT_HEIGHT + SEAL_RING_SIZE * 2,
        "l": USER_PROJECT_WIDTH + SEAL_RING_SIZE * 2,
    }
    pcell_var = layout.add_pcell_variant(lib, pcell_decl.id(), param)

    # Insert the seal ring for each project
    # (This should be part of the user project itself)
    top_cell.insert(
        pya.DCellInstArray(
            pcell_var,
            pya.DPoint(
                SPACING_HORIZONTAL - SEAL_RING_SIZE, SPACING_VERTICAL - SEAL_RING_SIZE
            ),
            pya.DVector(
                USER_PROJECT_WIDTH + SAW_STREET_VERTICAL + 2 * SEAL_RING_SIZE, 0
            ),
            pya.DVector(
                0, USER_PROJECT_HEIGHT + SAW_STREET_HORIZONTAL + 2 * SEAL_RING_SIZE
            ),
            8,
            5,
        )
    )

    # Write the final oasis
    layout.write("reticle.oas")


def main():

    pdk_root = os.environ.get("PDK_ROOT", None)
    pdk = os.environ.get("PDK", None)

    if not pdk_root or not pdk:
        print("Please export PDK_ROOT and PDK.")
        sys.exit()

    # Try to load the seal ring library
    sys.path.insert(
        1, os.path.join(pdk_root, pdk, "libs.tech", "klayout", "tech", "pymacros")
    )

    try:
        # Load the KLayout API based seal ring
        from seal_ring_cells import gf180mcu_seal_ring

        # Instantiate and register the library
        gf180mcu_seal_ring()
    except:
        print("Error: Couldn't load the seal ring library.")
        sys.exit()

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the user project layout.")
    parser.add_argument("cell", help="User project top-level cell.")
    args = parser.parse_args()

    stitch_reticle(args.path, args.cell)


if __name__ == "__main__":
    main()
