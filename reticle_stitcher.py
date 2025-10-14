# SPDX-FileCopyrightText: 2025 Wafer Space PTE. LTD. <info@wafer.space>
# SPDX-License-Identifier: Apache-2.0

import os
import csv
import sys
import hashlib
import argparse

import pya

# Constants
RETICLE_WIDTH = 32000
RETICLE_HEIGHT = 26000

SEAL_RING_SIZE = 26

USER_PROJECT_WIDTH = 3880
USER_PROJECT_HEIGHT = 5070

SAW_STREET_MINIMUM = 60

RETICLE_X_OFFSET = 124 / 2
RETICLE_Y_OFFSET = 150 / 2

BUF_SIZE = 65536


def read_data(manifest, tile_map):

    with open(manifest) as csvfile:
        dict_reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        headers = dict_reader.fieldnames

        data = list(dict_reader)

        manifest_data = {}

        # Set slot as key
        for entry in data:
            manifest_data[entry["SLOT"]] = entry

            # Check the hash
            md5 = hashlib.md5()

            with open(entry["SOURCE"], "rb") as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    md5.update(data)

            print("MD5: {0}".format(md5.hexdigest()))
            assert entry["HASH"] == md5.hexdigest()

    with open(tile_map) as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        tilemap_data = list(reader)

    print(manifest_data)
    print(tilemap_data)

    return manifest_data, tilemap_data

    def get_bounding_box(project_slot, tilemap_data):
        bb0 = None
        bb1 = None

        for y, row in enumerate(reversed(tilemap_data)):
            for x, slot in enumerate(row):
                if slot == project_slot:
                    if bb0 == None:
                        bb0 = [x, y]

                    if bb1 == None:
                        bb1 = [x, y]

                    if x < bb0[0]:
                        bb0[0] = x

                    if y < bb0[1]:
                        bb0[1] = y

                    if x > bb1[0]:
                        bb1[0] = x

                    if y > bb1[1]:
                        bb1[1] = y

        # make sure the project was found
        assert bb0
        assert bb1

        return bb0, bb1

    def get_num_tiles(project_slot, tilemap_data):
        num_tiles = 0

        for y, row in enumerate(reversed(tilemap_data)):
            for x, slot in enumerate(row):
                if slot == project_slot:
                    num_tiles += 1

        return num_tiles


def extract_size_position(manifest_data, tilemap_data):

    tile_map_width = len(tilemap_data[0])
    tile_map_height = len(tilemap_data)

    print(f"tile_map_width: {tile_map_width}")
    print(f"tile_map_height: {tile_map_height}")

    # Make sure all rows have the same size
    for row in tilemap_data:
        assert len(row) == tile_map_width

    # Get the tile size (with scribe line)
    tile_width = (
        8
        / tile_map_width
        * (USER_PROJECT_WIDTH + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )
    tile_height = (
        5
        / tile_map_height
        * (USER_PROJECT_HEIGHT + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )

    print(f"tile_width: {tile_width}")
    print(f"tile_height: {tile_height}")

    # For each slot in manifest, find the slot in the tile map and get the dimensions
    for slot in manifest_data:
        print(f"slot: {slot}")

        # Get the tile map
        bb0, bb1 = get_bounding_box(slot, tilemap_data)

        print(f"bb0: {bb0}, bb1: {bb1}")

        # Get the number of tiles
        num_tiles = get_num_tiles(slot, tilemap_data)

        # Calculate number of tiles in bounding box
        num_tiles_bb = (bb1[0] - bb0[0] + 1) * (bb1[1] - bb0[1] + 1)

        # Make sure projects are quare
        assert num_tiles == num_tiles_bb

        manifest_data[slot]["POSITION_TILES"] = bb0
        manifest_data[slot]["WIDTH_TILES"] = bb1[0] - bb0[0] + 1
        manifest_data[slot]["HEIGHT_TILES"] = bb1[1] - bb0[1] + 1

    return manifest_data


def create_reticle(manifest_data, tilemap_data, output_file="reticle.oas"):

    tile_map_width = len(tilemap_data[0])
    tile_map_height = len(tilemap_data)

    print(f"tile_map_width: {tile_map_width}")
    print(f"tile_map_height: {tile_map_height}")

    # Make sure all rows have the same size
    for row in tilemap_data:
        assert len(row) == tile_map_width

    # Get the tile size (with scribe line)
    tile_width = (
        8
        / tile_map_width
        * (USER_PROJECT_WIDTH + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )
    tile_height = (
        5
        / tile_map_height
        * (USER_PROJECT_HEIGHT + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )

    print(f"tile_width: {tile_width}")
    print(f"tile_height: {tile_height}")

    layout = pya.Layout()
    top_cell = layout.create_cell("reticle")

    # Create boundary (for debugging)
    PR_bndry = pya.LayerInfo(0, 0)
    top_cell.shapes(PR_bndry).insert(pya.DBox.new(0, 0, RETICLE_WIDTH, RETICLE_HEIGHT))

    for slot in manifest_data:

        project = manifest_data[slot]["PROJECT"]
        project_id = manifest_data[slot]["ID"]
        project_id_hash = manifest_data[slot]["HASH"]
        project_source = manifest_data[slot]["SOURCE"]

        x, y = manifest_data[slot]["POSITION_TILES"]

        print(
            f"Placing project {project} in {x}/{y}: {project_id} {project_id_hash} {project_source}"
        )

        # Create a separate layout to prevent cell conflicts
        user_layout = pya.Layout()

        # Read the user project
        user_layout.read(manifest_data[slot]["SOURCE"])
        user_layout_topcell = user_layout.top_cell()

        print(user_layout.top_cell().dbbox())

        x0 = user_layout.top_cell().dbbox().left
        y0 = user_layout.top_cell().dbbox().bottom
        x1 = user_layout.top_cell().dbbox().right
        y1 = user_layout.top_cell().dbbox().top

        # Check origin equals (0, 0)
        assert x0 == 0 and y0 == 0

        print(manifest_data[slot]["WIDTH_TILES"] * tile_width - SAW_STREET_MINIMUM)

        # Check dimensions of the project
        assert (
            manifest_data[slot]["WIDTH_TILES"] * tile_width - SAW_STREET_MINIMUM == x1
        )
        assert (
            manifest_data[slot]["HEIGHT_TILES"] * tile_height - SAW_STREET_MINIMUM == y1
        )

        # Create new cell in reticle layout
        user_cell = layout.create_cell(
            f"{user_layout_topcell.name}_{manifest_data[slot]['ID']}_{x}_{y}"
        )

        # Copy the contents into the cell
        user_cell.copy_tree(user_layout_topcell)

        # Insert the user cell
        top_cell.insert(
            pya.DCellInstArray(
                user_cell,
                pya.DPoint(
                    x * tile_width + RETICLE_X_OFFSET,
                    y * tile_height + RETICLE_Y_OFFSET,
                ),
            )
        )

    print(f"Writing reticle: {output_file}")

    # Write the final oasis
    layout.write(output_file)


def main():

    def is_valid_file(parser, arg):
        if not os.path.exists(arg):
            parser.error("The file %s does not exist!" % arg)
        else:
            return arg

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        help="The manifest CSV file.",
        metavar="FILE",
        type=lambda x: is_valid_file(parser, x),
    )
    parser.add_argument(
        "tile-map",
        help="The CSV tile map for the reticle.",
        metavar="FILE",
        type=lambda x: is_valid_file(parser, x),
    )

    args = vars(parser.parse_args())

    # Read the manifest
    manifest_data, tilemap_data = read_data(args["manifest"], args["tile-map"])

    # For each project get the tile position and size
    manifest_data = extract_size_position(manifest_data, tilemap_data)

    # Create the layout
    create_reticle(manifest_data, tilemap_data)


if __name__ == "__main__":
    main()
