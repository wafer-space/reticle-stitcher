MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
.PHONY: help

stitch: ## Stitch a reticle
	python3 reticle_stitcher.py examples/G801/manifest.csv examples/G801/tilemap_15x9.csv G801
.PHONY: stitch

stitch-obfuscate: ## Stitch a reticle
	python3 reticle_stitcher.py examples/G801/manifest.csv examples/G801/tilemap_15x9.csv G801 --obfuscate
.PHONY: stitch-obfuscate

stitch-empty: ## Stitch a reticle
	python3 reticle_stitcher.py examples/G801/manifest.csv examples/G801/tilemap_empty.csv G801
.PHONY: stitch-empty
