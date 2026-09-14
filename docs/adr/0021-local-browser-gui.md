# ADR-0021: One local browser GUI across deployment environments

- Status: accepted
- Date: 2026-08-26

## Decision

EWP Transcriber's GUI will be one self-contained local web application. A Python web adapter
serves bundled frontend assets and a versioned local API, while calling the existing
application services directly. WSL2, bare-metal Ubuntu, and the future Docker image use the
same frontend, API, domain models, and artifact formats.

The service binds to loopback by default and is initially single-user. Users select
server-visible user-space paths, avoiding browser copies of large media. The GUI rejects
symlinks and documented operating-system directories; optional search roots help native browser
pickers find a selected file but do not grant path authority. Docker later supplies paths through
explicit mounts. Remote multi-user hosting is not part of this decision.

## Context

The CLI has stabilized the canonical, revision, correction, translation, dictionary, audit,
and export contracts. The intended GUI must make these workflows accessible without creating
an alternate implementation or making users learn a different interface for each deployment
shape. A desktop toolkit would require environment-specific packaging and display behavior,
while a browser is already available across the target environments.

WSL also creates a meaningful boundary: the service and files live in Linux while the browser
normally runs on Windows. Docker introduces a similar host/container filesystem boundary.
Treating paths as server-side resources makes both cases explicit and avoids expensive,
privacy-sensitive uploads through the browser.

## Consequences

### Positive

- one UI can be tested once and reused across WSL2, Ubuntu, and Docker;
- the browser provides an accessible, familiar interaction model without a platform-specific
  desktop toolkit;
- existing application services and immutable artifacts remain authoritative;
- large local media need not be copied into browser-managed storage;
- frontend assets can remain offline, reproducible, and package-versioned;
- Docker becomes a distribution boundary rather than a new application architecture.

### Negative

- a local HTTP service introduces origin, CSRF, content-escaping, path-exposure, and lifecycle
  concerns that require explicit tests;
- host paths and container paths differ and must be explained clearly;
- browser security rules constrain direct filesystem and credential access;
- a JavaScript-capable browser is required for the interactive application.

## Rejected alternatives

### Separate desktop applications for Windows/WSL and Linux

Rejected because they would multiply packaging, UI testing, and behavior differences while
still needing the same application core.

### Build the GUI by invoking CLI subprocesses

Rejected because parsing terminal output would duplicate validation and state handling,
weaken typed diagnostics, and risk divergence from application-service behavior.

### Browser-first media upload

Rejected as the primary workflow because podcast media is already present locally, can be
large, and would be unnecessarily copied. A later opt-in upload feature is not prohibited.

### Start with a remotely accessible web service

Rejected because authentication, TLS, multi-user isolation, and hostile-network operation are
materially broader than a local production tool. They require a separate decision.

## Follow-up

The normative behavior and implementation sequence are specified in
[`../26-local-web-gui-contract.md`](../26-local-web-gui-contract.md).
