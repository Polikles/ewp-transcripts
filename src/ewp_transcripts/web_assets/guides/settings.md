# Settings & About

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Preferences and profile: Keep ETA off or enable it after calibration. Save, load or transfer one user-profile JSON with preferences, workspaces and dictionaries.
2. Test local dependencies: Run the optional environment test to enable Doctor and repair controls.
3. Read doctor report: Run doctor and inspect failed checks and technical details. Missing HF_TOKEN is harmless with complete offline models.
4. Repair only when needed: Reinstall dependencies opens terminal steps. Save work and stop the GUI before changing its environment.
5. Check application information: Check version, local processing, optional providers, licenses and notices.

## Detailed instructions

Diagnostics are maintenance tools, not required clicks in every transcription workflow. Tests run bounded child processes without downloading models or transcribing. Passing dependency checks does not qualify the complete GPU/model workflow.

Ubuntu 24.04 and 26.04 are accepted. The installation script automatically checks/repairs native audio libraries after installing locked dependencies. An OS upgrade can replace FFmpeg 6 with FFmpeg 8 while leaving the Python environment pinned to TorchCodec 0.7. See the Ubuntu upgrade guide when this occurs.

Repair uses bash scripts/repair-dependencies.sh in the transcription checkout. It preserves system FFmpeg, locked ML versions, model caches and previous artifacts. Keys are process-memory-only. Audio transcription is local; optional correction and translation send text only after explicit consent to the separately operated provider. No third-party retention guarantee is implied.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

In-progress feedback uses the owner-provided animated gear.svg motion mark, including global requests, adjacent button feedback, running statuses and active queue/card indicators. Its original reduced-motion behavior is preserved; completed/error markers are static.

## ETA and portable profiles

ETA becomes available only after three successful comparable complete transcriptions on the same
computer (language, models, speaker/track topology and execution phases must match). It remains
approximate. Elapsed and percentage are visible without ETA. Timing calibration is not transferred.

Save profile writes the current snapshot to the private local state directory. Load saved profile
restores it. Export profile saves and downloads ewp-user-profile.json; Import profile chooses that
single JSON in a browser picker. No media, transcripts, credentials, disclosure/verification consent,
active jobs or timing cache is embedded. Workspace records reference original external files.
Save transcript drafts separately before closing the program.

Profiles include the legacy private workspace catalog and the current saved-work catalog (the
output directory when its optional path is blank, or the explicitly selected custom catalog). Select
another catalog before making a separate export if needed. The selected dictionary library and
available dictionary files referenced by those workspaces are embedded, with original bytes/hash,
version and hidden status. Custom palette definitions are included. Missing files remain unavailable
references; no content is guessed or silently regenerated. The profile is limited to 16 MiB.

Import restores catalogs/preferences without running the queue or replacing the current editor.
Open Saved work & cleanup to choose a restored workspace. Missing paths are visibly unavailable;
restore their files (and original paths, or update a saved workspace copy) before loading. Dictionaries
are placed in content-addressed private directories, so an existing edition is not overwritten.
Independent dictionary import/export is also available in Dictionaries. Profile import merges saved
records; it does not delete existing workspaces, palettes or dictionary files.

## Temporary work directories

Open Temporary work directories and Refresh temporary inventory. Choose a retention reason and
minimum age in days, select unprotected rows, then Preview cleanup. Check the directory count/size
and Confirm deletion within five minutes. A change or new reference requires a new preview.
Creation time is the original allocation time, independent of the later retention reason.
Active tasks, known queue/workspace references, unknown files, final artifacts and legacy workdirs
without an owner timestamp are protected. A dead owner's workdir may show Interrupted.
Only the configured temporary root is inspected. References cover the current queue and default/
selected workspace catalogs; inspect other catalogs separately. This action is separate from
managed source-copy cleanup and never targets final output or model directories.

## Optional saved OpenRouter key

Manage OpenRouter key opens the same session-key dialog used by correction/translation. One key
serves all OpenRouter operations, including cloud ASR. Set session only keeps it in server
memory only. Save key deliberately retains it in the OS credential store on this computer; after
restarting, choose Use saved key. Remove saved key deletes that OS entry
and clears the active session key. Clear session key leaves a saved OS entry intact. An environment
key still applies until removed from the launching terminal; the UI reports that explicitly.

Windows uses Credential Manager (local-machine persistence). Linux/WSL requires an available
Secret Service; otherwise use the session-only option. No plaintext keyring fallback is used.
An OS unlock prompt may appear only when you request storage access. Profiles, workspaces,
transcripts, exports and browser storage never include keys.

Include dictionaries in profile is checked by default. Clear it for a smaller reference-only
profile; dictionary paths remain references and the exact editions must be transferred separately
using dictionary import/export. Profiles include named locations/recent project references.
Importing a profile does not create missing media directories or automatically start processing.


The key dialog has Close window, a top-right × and Escape. Closing clears unsubmitted input and
keeps any explicitly activated session/saved OS key. Set session only keeps the dialog
open so Check API key, Save and Use can follow before closing. Check API key verifies a typed key
without activating/saving it, or checks the current shared session/environment key when the input
is empty. Input is cleared immediately; the check uploads no audio/text and never accesses the OS
store implicitly. After restarting, enter a key or explicitly load a previously saved key.

Use saved key already activates the key for this server session. Set session only
is disabled when its text input is empty; type another key to enable it. Checking a typed key alone
does not activate/store it. Clearing browser/workflow state does not clear the active server key.
Stopping the server clears its memory-only key; an environment-supplied key can remain available,
and an OS-stored key can be explicitly loaded again. Saved work and profiles never contain keys.
Pending-media workspace references are included in profiles without embedding audio or approvals.

Save key and Use saved key share one row. Remove saved key and Clear session key are smaller,
secondary actions on the next row; Close window is at the bottom right. API-check feedback stays
to the right of Check API key, in two short lines. A cloud queue start also checks the active key before any local
media preparation or upload; an absent or rejected key leaves every queued job staged.
