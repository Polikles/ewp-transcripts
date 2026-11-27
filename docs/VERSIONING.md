# Version and delivery policy

One application version lives in `src/ewp_transcripts/_version.py`. Hatch reads it for package
metadata; CLI/GUI/doctor import the same value. uv watches that source for editable-build cache
invalidation. The dynamic project lock entry intentionally has no second version literal.

Before 1.0, increment MINOR for a handed-over feature set or incompatible change and PATCH for
compatible bug fixes. Document breaking changes explicitly. After 1.0, incompatible public API
changes increment MAJOR. See [SemVer](https://semver.org/spec/v2.0.0.html). Schema/API/dictionary/
model revision numbers are separate contracts, not app-version aliases.

Every identifiable build handed over for installation/manual testing has a distinct version.
Do not overwrite published artifacts or retag an existing version. The source SHA supplements the
version. Disposable uncommitted prototypes are explicitly marked source_dirty and are never
presented as a final installation/release. Local temporary version 0.22.1 used in lifecycle tests
was only a simulated version and must not be invented as historical delivery. The later actual
0.22.1 installer usability handoff has its own source/artifacts; that older simulation does not
qualify it.

For a new handoff:

1. Choose the next version in `_version.py`; move reviewed Unreleased changes into a dated section.
2. Update current README/manual version references and identical packaged help; preserve historical
   checkpoint/test evidence and already sent artist/installer archives.
3. Run `uv sync --locked`, `make check`, relevant integrations and installer-specific checks.
4. Commit reviewed sources, then build from that clean commit. `tools/build_setup.py` reads the
   version for bundle names/manifests and passes it to the Windows assembly/file version.
5. Verify archive checksums, native startup report and target-platform acceptance. Record exact
   source/toolchain, artifact digests and limits. Update checkpoint/TODO and push.
6. Publish a versioned GitHub release/tag only as a deliberate delivery step. Online bootstrap
   assets embed their corresponding payload hashes. Never upload different files under a released
   version; fixes require another version and artifacts.

0.21.0 consolidates the accepted workflow/manual changes since 0.20.0. 0.22.0 introduces managed
installation/distribution. The application workflow's prior acceptance does not automatically
qualify a new installer on Windows 11 or a different GPU. Code signing requires an appropriate
certificate and is separate from a successful build; current owner-test EXE is unsigned.

Owner revision2026-11-27 supersedes the previous signing prerequisite: the first several public
releases may be UNSIGNED. Later free OSS signing/owner-approved Actions integration is research,
not a release blocker or paid-certificate commitment. Actual signing procedure, private keys,
provider credentials and owner instructions remain outside this repository. Always describe actual
signing status accurately. Apply [release policy](RELEASE_POLICY.md) and the
[per-version checklist](RELEASE_CHECKLIST.md) to EVERY release, including changelog AND release
description, package-matched README/instructions/hardware/licenses/notices, evidence, final-byte
hashes/provenance and actual published-download verification. Attestations are prioritized early;
new automated enforcement is not yet implemented. Preserve original build bytes and provenance.
