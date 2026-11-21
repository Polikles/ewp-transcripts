# State, Errors, Logging, and Versioning

## 1. Working directory

Every job receives a directory in the WSL filesystem, for example:

```text
~/.cache/ewp-transcripts/work/<run_id>/<job_id>/
```

It may contain decoded WAV files, extracted channels, raw backend output, and diagnostic artifacts.

- after success: remove unless `--keep-temp` is used;
- after failure or cancellation: preserve;
- only final results are written to the output directory.

Allocation creates an owner-only `<work_root>/<run_id>/<job_id>/` directory with a small
ownership marker. Cleanup accepts only the exact typed workspace returned by allocation,
requires the marker to match its run and job identity, rejects symlinks, and removes only
that job directory. It never recursively removes the work root, run root, output
directory, model cache, or siblings.

## 2. Atomic writes

1. Create the work directory.
2. Write state to `_results.partial.json.tmp`.
3. Flush and `fsync` when available.
4. Rename to `_results.partial.json`.
5. After success, create a final temporary file in the destination directory.
6. Validate it against the schema.
7. Atomically rename it to `_results.json`.

The reservation implementation publishes the initial running state with an
exclusive same-filesystem hard link from a fully written and `fsync`ed temporary file.
This provides no-overwrite semantics unavailable from a normal replacing rename. The
directory is then `fsync`ed on POSIX before the temporary link is removed. Native Windows skips
unsupported directory-descriptor operations while keeping file flushes and atomic publication;
directory-metadata durability after power loss is not claimed there. Reservation is planned
again while holding the output-directory lock, so a stale dry-run decision is never used
for mutation.

On filesystems or mounts without reliable atomic rename semantics, the implementation must emit a warning and use a safe copy-and-verify strategy.

## 3. Existing-result lookup

The application searches the output directory for `results*.json` and compares `episode_signature_sha256`.

### Same signature

- without `--force`: warning and SKIP;
- with `--force`: create `_v002`, `_v003`, and so on.

### Same job ID, different signature

A new version is created automatically because the source differs. The application emits a source-name collision warning.

### Same signature, different source filename

This is still a duplicate. Without `--force`, the job is skipped and the existing result is reported.

## 4. Version allocation

- no suffix means version 1;
- the first additional version is `_v002`;
- numbers use at least three digits through 999;
- allocation occurs while holding an output-directory lock;
- every file created by one run uses the same version number.

## 5. Batch errors

- failure of one job is recorded and the batch continues;
- the summary contains Completed, Skipped, Warnings, Failed, and Cancelled counts;
- the process returns a non-zero exit code when at least one job failed;
- `Ctrl+C` marks the current job as `cancelled`, removes temporary files being finalized, and stops the queue.

## 6. Warning and error codes

Implemented user-visible diagnostics use stable codes and are documented in the
[warning and error code catalogue](25-warning-error-catalog.md). Codes previously listed as
aspirational minimums are not presented as implemented until an emitting path and test exist.
Human-readable wording may improve, but a published code must not silently change meaning.

## 7. Logging

Default format: human-readable text. Optional format: JSON Lines.

For `transcribe`, `runtime.log_format = "jsonl"` makes application outcome records on
standard output valid JSON Lines. Incidental backend/model output is redirected to standard error
so it cannot corrupt a machine-readable stdout stream. Single-job completion/skip records and
per-job plus batch-summary records include elapsed milliseconds; detailed stage durations and the
observed PyTorch CUDA allocation peak remain in the canonical result JSON.

Every structured record should include:

- timestamp;
- level;
- event code;
- `run_id`;
- `job_id`;
- source when relevant;
- stage;
- elapsed time;
- safe context.

Logs MUST NOT contain:

- `HF_TOKEN`;
- full transcript text by default;
- audio content;
- arbitrary environment dumps.

## 8. Locks

The application MUST prevent concurrent writes to the same output directory.

Mutable storage operations use a persistent `.ewp-transcripts.lock` file in the resolved
output directory and an exclusive Linux/WSL `flock`. The lock file stores only the holder
PID and acquisition timestamp. It is not deleted on release: retaining one inode avoids a
race in which a waiter holds the old inode while a new process locks a replacement file.
Kernel lock ownership is authoritative, so a leftover metadata timestamp does not itself
mean the directory is locked. The configured timeout controls how long acquisition waits;
the MVP default of zero fails immediately.

Transitions to `failed` or `cancelled` reacquire the same directory lock and verify the
persisted run ID, job ID, episode signature, version, and current `running` status against
the in-memory reservation. A complete terminal record is published exclusively before
the running record is removed. If cleanup is interrupted, both parseable records may
remain and the version stays occupied; neither record is overwritten.

## 9. Workdir cleanup metadata

New allocations use marker version `2.0`: run/job identity, immutable UTC `created_at`,
`owner_pid`, and `retention_reason`. Allocation writes `active`; the owning process atomically
records `failed`, `cancelled`, or `successful-retained` when preserving a finished workdir.
These metadata changes never alter the creation time. Version-2 age filters use creation time.
Version-1 markers remain readable and structurally valid; their creation time/reason is unknown,
and legacy age discovery retains the old marker-mtime interpretation.

The GUI inventories only the configured temporary root. It separately filters by age/reason,
selects eligible workdirs, previews identities/size, and requires explicit confirmation within
five minutes. Before deleting any selected path, it rechecks the entire selection's markers,
file metadata and references. A changed/protected selection invalidates the preview. I/O failure
reports the successfully removed subset. No automatic cleanup runs.

Active owner processes, current queue paths, default/selected saved-workspace references,
symlinks, special files and unknown artifacts are protected. The current pipeline owns only WAV
intermediates plus its marker; any other file protects that entire directory. A dead owner's active
marker is displayed as interrupted; PID reuse may conservatively keep it protected. Catalogs stored
elsewhere are unknown: select/check them separately. Final results, revisions, translations, models
and durable browser source copies are not temporary-workdir cleanup targets.

Version-1 markers lack proof of owner liveness and remain visible but protected in bulk GUI/CLI
cleanup. Inspect any old retained workspace manually before explicitly removing its exact directory
outside the bulk tool. The existing low-level owner-marker validator/cleanup remains compatible
with both versions. `clean all-workdirs --dry-run/--yes` now skips active, legacy-unknown and unsafe/
unknown-artifact workdirs too; its CLI JSON/text shape is unchanged. The GUI additionally checks
known saved-work references; the CLI does not inventory GUI workspace catalogs.


## 10. Revision state and publication (implemented for v0.2.0)

Transcript revisions are final immutable artifacts and use the same non-destructive
persistence principles as canonical outputs. Revision number allocation occurs under the
output-directory lock. A final revision is schema-validated before atomic publication and
never overwrites an existing revision.

Preview and `apply --no-apply` do not reserve a permanent revision number. Review work
files are user-editable and are not treated as final application state.

A revision verifies the exact SHA-256 of its canonical base before application or export.
A parent revision hash is provenance; the parent is not needed to materialize the child.

Implemented revision warning/error codes include:

```text
REVISION_ALIGNMENT_AMBIGUOUS
REVISION_ANCHOR_INVALID
REVISION_INSERT_ACROSS_LONG_GAP
REVISION_SPEAKER_INVALID
```

Other incompatible revision conditions use `INVALID_REVISION`; the detailed message names
the failed lineage or content check.

Batch prepare/apply follows the existing failure-isolation policy and returns the existing
batch-failure exit code when one or more items fail.
