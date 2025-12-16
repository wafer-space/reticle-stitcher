# SPDX-FileCopyrightText: 2025 Wafer Space PTE. LTD. <info@wafer.space>
# SPDX-License-Identifier: Apache-2.0

import os
import pya
import csv
import sys
import random
import hashlib
import argparse
import subprocess
from dataclasses import dataclass

# Constants
# RETICLE_WIDTH = 32000
# RETICLE_HEIGHT = 26000
RETICLE_WIDTH = 30000
RETICLE_HEIGHT = 24000

SEAL_RING_SIZE = 26

USER_PROJECT_WIDTH = 3880
USER_PROJECT_HEIGHT = 5070

USER_DIE_WIDTH = USER_PROJECT_WIDTH + 2 * SEAL_RING_SIZE
USER_DIE_HEIGHT = USER_PROJECT_HEIGHT + 2 * SEAL_RING_SIZE

SAW_STREET_MINIMUM = 60
SAW_STREET = 60

assert SAW_STREET >= SAW_STREET_MINIMUM

TILE_GRID = 2

TILE_WIDTH = (USER_DIE_WIDTH - ((TILE_GRID - 1) * SAW_STREET)) / TILE_GRID
TILE_HEIGHT = (USER_DIE_HEIGHT - ((TILE_GRID - 1) * SAW_STREET)) / TILE_GRID

tile_pitch_x = TILE_WIDTH + SAW_STREET
tile_pitch_y = TILE_HEIGHT + SAW_STREET

RETICLE_X_OFFSET = 60
RETICLE_Y_OFFSET = 60

BUF_SIZE = 65536

SLOT_TO_TEXT_SIZE = {
    "1x1": 1,
    "1x0p5": 1,
    "0p5x1": 0.7,
    "0p5x0p5": 0.7,
}

COLORS = [
    "#1c284d",
    "#343473",
    "#2d5280",
    "#4d7a99",
    "#7497a6",
    "#a3ccd9",
    "#f0edd8",
    "#732866",
    "#a6216e",
    "#d94c87",
    "#d9214f",
    "#f25565",
    "#f27961",
    "#993649",
    "#b36159",
    "#f09c60",
    "#b38f24",
    "#b3b324",
    "#f7c93e",
    "#17735f",
    "#119955",
    "#67b31b",
    "#1ba683",
    "#47cca9",
    "#96e3c9",
    "#2469b3",
    "#0b8be6",
    "#0bafe6",
    "#f28d85",
    "#f0bb90",
]


class Project:
    REQUIRED_ENTRIES = ["CODE", "PROJECT", "SLOT_SIZE", "TOP", "SHA256", "LAYOUT"]

    SLOT_TO_TILES = {
        "1x1": (2, 2),
        "1x0p5": (2, 1),
        "0p5x1": (1, 2),
        "0p5x0p5": (1, 1),
    }

    code: str
    project: str
    slot: str
    top: str
    hash_md5: str
    layout: str

    tiles_width: int
    tiles_height: int

    width: float
    height: float

    def __init__(self, entries):

        # Make sure the required entries exist
        assert all(x in self.REQUIRED_ENTRIES for x in entries)

        self.code = entries["CODE"]
        self.project = entries["PROJECT"]
        self.slot = entries["SLOT_SIZE"]
        self.top = entries["TOP"]
        self.hash_md5 = entries["SHA256"]
        self.layout = entries["LAYOUT"]

        # Make sure the slot size is valid
        if not self.slot in self.SLOT_TO_TILES:
            print(f"Error: invalid slot size: '{self.slot}'")
            sys.exit(-1)

        self.tiles_width, self.tiles_height = self.SLOT_TO_TILES[self.slot]

        # Calculate the size of the layout
        self.width = self.tiles_width * TILE_WIDTH + SAW_STREET * (self.tiles_width - 1)
        self.height = self.tiles_height * TILE_HEIGHT + SAW_STREET * (
            self.tiles_height - 1
        )

    def __repr__(self):
        return f"Project({self.code}, {self.project}, {self.slot}, {self.top}, {self.hash_md5}, {self.layout}, {self.tiles_width}, {self.tiles_height})"


def read_manifest(base_path, manifest):

    with open(manifest) as csvfile:
        dict_reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        headers = dict_reader.fieldnames

        data = list(dict_reader)

        projects = {}

        # Set slot as key
        for entry in data:
            projects[entry["CODE"]] = Project(entry)

            # Check the hash
            sha256 = hashlib.sha256()

            layout_path = os.path.join(base_path, entry["LAYOUT"])
            print(f"Checking hash for: {layout_path}")

            with open(layout_path, "rb") as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha256.update(data)

            print("Actual SHA256: {0}".format(sha256.hexdigest()))
            print("Expected SHA256: {0}".format(entry["SHA256"]))
            assert entry["SHA256"] == sha256.hexdigest()

    return projects


def read_tilemap(tile_map):
    with open(tile_map) as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        tilemap_data = list(reader)

    return tilemap_data


class SVG:

    @dataclass
    class Box:
        x: float
        y: float
        width: float
        height: float
        fill: str

    @dataclass
    class Text:
        x: float
        y: float
        fill: str
        text: str
        size: float

    boxes: list[Box]
    texts: list[Text]

    def __init__(self, width, height, fill):
        self.boxes = []
        self.texts = []
        self.width = width
        self.height = height
        self.fill = fill

    def draw_rect(self, x, y, width, height, fill="#FF00FF"):
        self.boxes.append(self.Box(x, y, width, height, fill))

    def draw_text(self, x, y, fill, text, size=1):
        self.texts.append(self.Text(x, y, fill, text, size))

    def save(self, path):
        with open(path, "w") as file:
            file.write(
                f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>

<svg
   width="{self.width}mm"
   height="{self.height}mm"
   viewBox="0 0 {self.width} {self.height}"
   version="1.1"
   id="svg1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">\n"""
            )

            file.write("  <g>\n")

            file.write(
                f"""    <rect
       style="fill:{self.fill};fill-opacity:1"
       id="rect1"
       width="{self.width}"
       height="{self.height}"
       x="0"
       y="0" />\n"""
            )

            for box in self.boxes:
                file.write(
                    f"""    <rect
       style="fill:{box.fill};fill-opacity:1"
       id="rect1"
       width="{box.width}"
       height="{box.height}"
       x="{box.x}"
       y="{box.y}" />\n"""
                )

            for text in self.texts:
                file.write(
                    f"""<text
       xml:space="preserve"
       style="font-size:{text.size}px;text-align:start;writing-mode:lr-tb;direction:ltr;text-anchor:start;fill:{text.fill};fill-opacity:1"
       x="{text.x}"
       y="{text.y}"
       id="text2"><tspan
          id="tspan2"
          style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:{text.size}px;font-family:'Adwaita Mono', 'Courier New', 'Lucida Console';text-align:center;text-anchor:middle;fill:{text.fill};fill-opacity:1"
          x="{text.x}"
          y="{text.y}">{text.text}</tspan></text>\n"""
                )

            file.write("  </g>\n")
            file.write("</svg>\n")


def create_reticle(
    base_path,
    projects,
    tilemap_data,
    output_file="reticle.gds",
    output_svg="reticle.svg",
):

    tile_map_width = len(tilemap_data[0])
    tile_map_height = len(tilemap_data)

    print(f"tile_map_width: {tile_map_width}")
    print(f"tile_map_height: {tile_map_height}")

    # Make sure all rows have the same size
    for row in tilemap_data:
        assert len(row) == tile_map_width

    # Create a second tile map for valid look-up
    valid_tilemap = [[1 for x in range(tile_map_width)] for y in range(tile_map_height)]

    layout = pya.Layout()
    top_cell = layout.create_cell("reticle")

    svg_object = SVG(RETICLE_WIDTH / 1000, RETICLE_HEIGHT / 1000, "#FFFFFF")

    # Create boundary
    PR_bndry = pya.LayerInfo(0, 0)
    top_cell.shapes(PR_bndry).insert(pya.DBox.new(0, 0, RETICLE_WIDTH, RETICLE_HEIGHT))

    # Iterate over all tiles
    for y, row in enumerate(reversed(tilemap_data)):
        for x, code in enumerate(row):
            print(f"Tile: {x}/{y}: '{code}'")

            # Skip empty tiles
            if not code:
                continue

            # Skip invalid tiles
            if not valid_tilemap[y][x]:
                continue

            if not code in projects:
                print(f"[Warning]: {code} does not exist in projects.")
                continue

            assert code in projects
            project = projects[code]

            print(f"{x}/{y}: Placing {project}")

            # Create a separate layout to prevent cell conflicts
            user_layout = pya.Layout()

            # Read the user project
            layout_path = os.path.join(base_path, project.layout)
            print(f"Reading layout: {layout_path}")
            user_layout.read(layout_path)

            # Get the top cell
            user_layout_topcell = user_layout.top_cell()
            assert user_layout_topcell.name == project.top

            dbbox = user_layout.top_cell().dbbox()

            # Check origin equals (0, 0)
            assert dbbox.left == 0 and dbbox.bottom == 0

            # Check the layout size
            assert project.width == dbbox.width()
            assert project.height == dbbox.height()

            # Create new cell in reticle layout
            user_cell = layout.create_cell(f"{project.code}_{project.top}_{x}_{y}")

            # Copy the contents into the cell
            user_cell.copy_tree(user_layout_topcell)

            # Insert the user cell
            top_cell.insert(
                pya.DCellInstArray(
                    user_cell,
                    pya.DPoint(
                        x * tile_pitch_x + RETICLE_X_OFFSET,
                        y * tile_pitch_y + RETICLE_Y_OFFSET,
                    ),
                )
            )

            color = COLORS[random.randint(0, len(COLORS) - 1)]

            svg_object.draw_rect(
                (x * tile_pitch_x + RETICLE_X_OFFSET) / 1000,
                (
                    RETICLE_HEIGHT
                    - (project.height + y * tile_pitch_y + RETICLE_Y_OFFSET)
                )
                / 1000,
                project.width / 1000,
                project.height / 1000,
                fill=color,
            )

            text_size = SLOT_TO_TEXT_SIZE[project.slot]

            svg_object.draw_text(
                (x * tile_pitch_x + RETICLE_X_OFFSET + project.width / 2) / 1000,
                (
                    RETICLE_HEIGHT
                    - (
                        +project.height
                        - project.height / 2.2
                        + y * tile_pitch_y
                        + RETICLE_Y_OFFSET
                    )
                )
                / 1000
                + text_size / 2,
                fill="#FFFFFF",
                text=project.code,
                size=text_size,
            )

            def invalidate_tilemap(valid_tilemap, x, y, tiles_width, tiles_height):
                for x_offset in range(project.tiles_width):
                    for y_offset in range(project.tiles_height):
                        valid_tilemap[y + y_offset][x + x_offset] = 0

            # Invalidate tiles in valid tile map
            invalidate_tilemap(
                valid_tilemap, x, y, project.tiles_width, project.tiles_height
            )

    # Write the SVG
    svg_object.save(output_svg)

    # Write the final oasis
    print(f"Writing reticle: {output_file}")
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
    parser.add_argument(
        "output",
        help="Output name of the reticle layout.",
        nargs="?",
        default="reticle.oas",
    )

    parser.add_argument(
        "output-filled",
        help="Output name of the filled reticle layout.",
        nargs="?",
        default="reticle_filled.oas",
    )

    parser.add_argument(
        "svg",
        help="Output name of the svg.",
        nargs="?",
        default="reticle.svg",
    )

    # Parse the arguments
    args = vars(parser.parse_args())

    # Get the base path
    base_path = os.path.realpath(os.path.dirname(args["manifest"]))
    print(f"Manifest base path: {base_path}")

    # Read the manifest
    projects = read_manifest(base_path, args["manifest"])
    tilemap = read_tilemap(args["tile-map"])

    # Create the reticle layout
    create_reticle(base_path, projects, tilemap, args["output"], args["svg"])

    macro = os.path.join(os.path.dirname(__file__), "scripts", "fill.py")
    subprocess.run(
        [
            "klayout",
            "-b",
            "-r",
            macro,
            "-rd",
            f"input={args['output']}",
            "-rd",
            f"output={args['output-filled']}",
        ]
    )


if __name__ == "__main__":
    main()
