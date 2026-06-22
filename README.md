# Reticle Stitcher

Tool for stitching a full MPW reticle using gf180mcu for delivery to a foundry.

## Usage

Enable the Nix shell:

```
nix-shell
```

To run the stitcher, supply the manifest and tile map and specify the reticle/shuttle name:

```
python3 reticle_stitcher.py G801/manifest.csv G801/tilemap.csv G801
```

To generate the obfuscated reticle, pass `--obfuscate` as argument.
You can find all output files under `runs/<timestamp>/` relative to the current working directory.
Use `--run-tag` to set a manual run tag, else the current tiem and date is used.

## File Structure

The following file structure should be created for each shuttle:

```
G801
|-- tilemap.csv
|-- manifest.csv
|-- MOLE
|   |-- chip_top.oas
|-- KIAN
|   |-- layout.oas
|-- CAFE
|   |-- chip.oas
...
```

## Manifest

The manifest contains a list of all projects.

The following entries are required in the CSV file:

- CODE: the project code (e.g. `MOLE`, `KIAN`, `CAFE`)
- PROJECT: the project name
- SLOT_SIZE: one of `1x1`, `1x0p5`, `0p5x1`, `0p5x0p5`
- TOP: top-cell name
- SHA256: sha256 hash of the layout file in the `LAYOUT` field
- LAYOUT: relative path (from the manifest) to the chip layout (e.g. `MOLE/chip_top.oas`)

The following entries are optional in the CSV file:

- VISIBILITY: the project visibility (e.g. `Public` or `Private`). If the reticle is obfuscated, this key decides whether the layout will be inserted or not.
- PROJECT_DETAILS: a long description of the project
- REPOSITORY: a URL to the project repository

These are the required entries. However, additional entries can be added for documentation purposes.

| CODE | PROJECT                                  | SLOT_SIZE | TOP      | SHA256                           | LAYOUT                  |
|------|------------------------------------------|-----------|----------|----------------------------------|-------------------------|
| MOLE | FABulous FPGA                            | 1x1       | chip_top | 65870f9152cfa47762051575c2ba6436 | MOLE/chip_top.gds       |
| TQVC | TinyQV - Crowdsourced Risc-V SoC (1x0.5) | 1x0p5     | chip_top | 20a50d0bd648c4108a028aa50bac09e5 | TQVC/tinyqv_hheight.gds |
| TQVB | TinyQV - Crowdsourced Risc-V SoC (0.5x1) | 0p5x1     | chip_top | 55b12cdcd16b311bcd955b6351456982 | TQVB/tinyqv_hwidth.gds  |
| TQVA | TinyQV - Crowdsourced Risc-V SoC         | 0p5x0p5   | chip_top | 5daddac8767234c75d0aa03b2e11d89b | TQVA/tinyqv_quarter.gds |
| ... | ... | ... | ... | ... | ... |

## Tile Map

The tile map is the mapping from project to tile location.

| JKU2 | JKU2 | OCD2 | OCD2 | AMOS | AMOS |      |      |      |      | GD04 | GD04 | TQVC | TQVC | TQVA |
|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|
| 2975 | 2975 | 2975 | 2975 | AF01 | AF01 | GD03 | GD03 | OCD1 | OCD1 |      |      | RBOY | RBOY | TQVB |
| 2975 | 2975 | 2975 | 2975 | AF01 | AF01 | GD03 | GD03 | OCD1 | OCD1 |      |      | RBOY | RBOY | TQVB |
| TZ01 | TZ01 | TZ01 | TZ01 | AF01 | AF01 | TTP2 | TTP2 | MOLE | MOLE | CHES | CHES | ISHI | ISHI | GD02 |
| TZ01 | TZ01 | TZ01 | TZ01 | AF01 | AF01 | TTP2 | TTP2 | MOLE | MOLE | CHES | CHES | ISHI | ISHI | GD02 |
| RZ80 | RZ80 | RZ80 | RZ80 | MOSB | MOSB | TTPG | TTPG | BRWN | BRWN |      |      | RZML | RZML | TRID |
| RZ80 | RZ80 | RZ80 | RZ80 | MOSB | MOSB | TTPG | TTPG | BRWN | BRWN |      |      | RZML | RZML | TRID |
| BTAP | BTAP | BTAP | BTAP | MOSB | MOSB | AS03 | AS03 | KIAN | KIAN | JKU1 | JKU1 | CAFE | CAFE | HZ80 |
| BTAP | BTAP | BTAP | BTAP | MOSB | MOSB | AS03 | AS03 | KIAN | KIAN | JKU1 | JKU1 | CAFE | CAFE | HZ80 |


- A 1x1 slot is 2x2 tiles.
- A 0.5x1 slot is 1x2 tiles.
- A 1x0.5 slot is 2x1 tiles.
- A 0.5x0.5 slot is 1x1 tiles.
