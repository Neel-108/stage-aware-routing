# Decisions

D1 (2026-11-13): Reuse the Loc2Repair baseline unchanged, pinned at commit 399b4dca53e6dc3e06c4531be3222dc7ec4d4d3f.

D2 (2026-11-13): Mohammad's code stays in ~/nir/loc2repair and is never edited. Our work lives in this repo.
D3 (2026-11-14): .env lives in this repo (git-ignored). Load only the secrets each step needs.
D4 (2026-11-14): Sandbox network is bridge. A container reached the ITMO endpoint without host networking.
D5 (2026-11-14): Loc2Repair runs commands from its own folder, so every path passed to it must be absolute and point into this repo.

D2 (2026-11-13): Mohammad's code stays in ~/nir/loc2repair and is never edited. This research work lives in this repo.
D3 (2026-11-14): .env lives in this repo (git-ignored). Load only the secrets each step needs.
D4 (2026-11-14): Sandbox network is bridge. A container reached the ITMO endpoint without host networking.
D5 (2026-11-14): Loc2Repair runs commands from its own folder, so every path passed to it must be absolute and point into this repo.
