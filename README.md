# Reticle Stitcher

Tool for stitching a full MPW reticle using gf180mcu for delivery to a foundry.

> [!WARNING]
> This tool is WIP.

## Usage

To run the stitcher, supply the manifest and tile map:

```
python3 reticle_stitcher.py manifest-wsmpw1.csv tilemap-wsmpw1.csv
```

## Manifest

The manifest contains a list of all projects.

| SLOT | PROJECT  | ID | HASH                             | SOURCE                         |
|------|----------|----|----------------------------------|--------------------------------|
| 1    | project1 | 00000001  | 85eb8b0773f59442c36db690c865bda7 | chips/00000001/chip_top.gds.gz |
| 2    | project2 | 00000002  | 428e06ac9c44dd2e1938d1e345ded193 | chips/00000002/chip_top.gds.gz |
| ...  | ...      | ... | ...                             | ...                            |

For the hash MD5 is used, as it is fast and only used for file validation.

## Tile Map

The tile map is the mapping from slot to tile location.

|    |    |    |    |    |    |    |    |
|----|----|----|----|----|----|----|----|
| 33 | 34 | 35 | 36 | 37 | 38 | 39 | 40 |
| 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
| 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| 9  | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
| 1  | 2  | 3  | 4  | 5  | 6  | 7  | 8  |
