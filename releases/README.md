# Releases index — storage decision pending

This directory exists for the planned versioned distribution index. There is no public product
release or downloadable binary here yet. Do not commit the current ~142 MB EXE as an ordinary Git
blob: it exceeds GitHub's100 MiB limit.

Proposed structure, pending owner agreement: releases/<version>/ notes/metadata/SHA256 and links
to actual GitHub Release assets. Keep at least2–3 downloadable versions; agree older archival and
retain source/provenance/checksums. Possible later MSIX/DEB assets are not current deliverables.
LFS requires a separate quota/billing decision and has not been enabled.

See [release policy](../docs/RELEASE_POLICY.md) and [roadmap](../docs/99-roadmap-v2.md).
