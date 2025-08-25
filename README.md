# reticle-stitcher

Tool for stitching a full MPW reticle using gf180mcu for delivery to a foundry.

> [!WARNING]  
> This tool is WIP.

First you need to export:

```
export PDK_ROOT=/path/to/pdks
export PDK_ROOT=gf180mcuD
```

For now, the stitcher only supports a single project replicated across all 40 slots.

To run the stitcher, supply the user project and the top cell name:

```
python3 reticle_stitcher.py caravel_18019f00.oas caravel_18019f00
```