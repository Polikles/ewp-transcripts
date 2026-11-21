# B6 optional shared OS credentials

Date: 2026-11-21. Baseline eee6ef9. Agent implementation/checks complete; native secure-store
execution is part of owner B9 acceptance, not claimed from Linux mocks.

One OpenRouter server-session key is reused by correction/translation and the later ASR adapter.
The existing session endpoint remains compatible; explicit save/use/remove/clear-session actions
add OS persistence. Windows uses the built-in Credential Manager backend with local-machine
persistence; Linux/WSL uses built-in Secret Service. Third-party/plaintext keyring selection is
never automatic. There is no real-store access on startup: the user explicitly chooses Use saved
OpenRouter key after a restart, avoiding unsolicited unlock prompts/headless startup hangs.

Settings & About and the shared provider dialog expose the controls. Inputs clear after submit,
failure and dialog close. Backend exceptions are sanitized, responses never return keys and
profile/workspace/export fields remain allowlisted/credential-free. Removing saved/session keys
does not mutate the launching terminal's environment; remaining environment fallback is visible.

Verification: make check PASS, Ruff/format, mypy 108 source files, 937 tests. Synthetic OS-backend
tests cover no startup access, same-entry persistence across store lifetimes, deletion, missing
entry, unavailable backend and exception redaction. Packaged changed-step guide matches source.
Real HTTP/CSRF/browser controls receive the integrated B9 check. No actual user OS key was read,
written or removed; no provider call was made. Keyring 25.7.0 locked with OS-specific dependencies.
Reference: https://keyring.readthedocs.io/en/latest/ and the tagged Windows/SecretService sources.

Next: B7 projects/locations/canonical directory scanning and dictionary-free profile export.
