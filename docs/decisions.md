# Decisions

D1 (2026-11-13): I reuse the Loc2Repair baseline unchanged, pinned at commit 399b4dca53e6dc3e06c4531be3222dc7ec4d4d3f.

D2 (2026-11-13): The Loc2Repair code stays in its own folder (~/nir/loc2repair) and is never edited. All my work lives in this repository.

D3 (2026-11-14): The .env file lives in this repository and is ignored by Git. Each step loads only the secrets it needs.

D4 (2026-11-14): The sandbox uses Docker's bridge network. A test container reached the model endpoint without host networking.

D5 (2026-11-14): Loc2Repair runs its commands from its own folder, so every path I pass to it is absolute and points into this repository.
